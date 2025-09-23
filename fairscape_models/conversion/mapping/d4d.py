from datetime import datetime
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from fairscape_models.conversion.models.d4d import DatasetCollection, Dataset, FormatEnum
from fairscape_models.rocrate import ROCrateV1_2

def parse_authors_from_ro_crate(authors: Any) -> List[str]:
    if not authors: return []
    if isinstance(authors, str):
        return [name.strip() for name in authors.replace(';', ',').split(',') if name.strip()]
    elif isinstance(authors, list):
        return [str(item) for item in authors]
    return []

def parse_funders_from_ro_crate(funders: Any) -> List[str]:
    if not funders: return []
    if isinstance(funders, str):
        return [part.strip() for part in re.split(r'\.\s*|[;,]', funders) if part.strip()]
    elif isinstance(funders, list):
        return [str(item) for item in funders]
    return []

def parse_keywords_simple(keywords: Any) -> List[str]:
    if not keywords: return []
    if isinstance(keywords, str):
        return [kw.strip() for kw in re.split(r'[;,]', keywords) if kw.strip()]
    elif isinstance(keywords, list):
        return [str(item) for item in keywords]
    return []

def parse_related_publications(value_from_lookup: Any) -> List[str]:
    if not value_from_lookup: return []
    pubs = []
    items_to_process = value_from_lookup if isinstance(value_from_lookup, list) else [value_from_lookup]
    
    for pub in items_to_process:
        if isinstance(pub, dict):
            citation = pub.get("citation") or pub.get("name") or pub.get("@id")
            if citation: pubs.append(str(citation))
        elif isinstance(pub, str) and pub.strip():
            pubs.append(pub.strip())
    return pubs

def parse_file_size_to_bytes(size_value: Any) -> Optional[int]:
    if size_value is None:
        return None
    if isinstance(size_value, int):
        return size_value
    if isinstance(size_value, str):
        size_str = size_value.strip().lower()
        if size_str.isdigit():
            return int(size_str)
        
        units = {
            'b': 1, 'byte': 1, 'bytes': 1,
            'kb': 1024, 'kilobyte': 1024, 'kilobytes': 1024,
            'mb': 1024**2, 'megabyte': 1024**2, 'megabytes': 1024**2,
            'gb': 1024**3, 'gigabyte': 1024**3, 'gigabytes': 1024**3,
            'tb': 1024**4, 'terabyte': 1024**4, 'terabytes': 1024**4
        }
        
        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                try:
                    number = float(size_str[:-len(unit)].strip())
                    return int(number * multiplier)
                except ValueError:
                    continue
    return None

def from_additional_property(name: str, default: Optional[str] = None):
    def _parser(prop_list: Any) -> Optional[str]:
        if isinstance(prop_list, list):
            for p in prop_list:
                if isinstance(p, dict) and p.get("name") == name:
                    val = p.get("value")
                    return str(val) if val is not None else default
        return default
    return _parser

def _build_datasets_from_subcrates(*, converter_instance, source_entity_model) -> List[Dataset]:
    """Build Dataset objects from sub-crates, with sub-crate properties taking precedence."""
    datasets = []
    root_dict = source_entity_model.model_dump(by_alias=True)
    
    release_properties = {
        "version": root_dict.get("version"),
        "license": root_dict.get("license"),
        "keywords": parse_keywords_simple(root_dict.get("keywords")),
        "created_on": root_dict.get("datePublished"),
        "issued": root_dict.get("datePublished"),
        "publisher": root_dict.get("publisher"),
        "doi": root_dict.get("identifier"),
        "creators": parse_authors_from_ro_crate(root_dict.get("author")),
        "funders": parse_funders_from_ro_crate(root_dict.get("funder")),
        "purposes": root_dict.get("rai:dataUseCases"),
        "tasks": root_dict.get("rai:dataLimitations"),
        "ethical_reviews": root_dict.get("ethicalReview"),
        "discouraged_uses": from_additional_property("Prohibited Uses")(root_dict.get("additionalProperty")),
        "updates": root_dict.get("rai:dataReleaseMaintenancePlan"),
        "sensitive_info": root_dict.get("rai:personalSensitiveInformation"),
    }
    
    subcrate_entities = [
        e for e in converter_instance.source_crate.metadataGraph
        if hasattr(e, 'ro-crate-metadata') and e.guid != "ro-crate-metadata.json"
    ]
    
    for subcrate_entity in subcrate_entities:
        subcrate_dict = subcrate_entity.model_dump(by_alias=True)
        metadata_path = getattr(subcrate_entity, 'ro-crate-metadata', None)
        
        dataset_args = {
            "id": subcrate_dict.get("@id", f"subcrate-{len(datasets)}"),
            "title": subcrate_dict.get("name", "Unnamed Subcrate"),
            "description": subcrate_dict.get("description"),
            "download_url": subcrate_dict.get("contentUrl"),
            "path": subcrate_dict.get("contentUrl"),
            "bytes": parse_file_size_to_bytes(subcrate_dict.get("contentSize")),
            "md5": subcrate_dict.get("md5"),
            **release_properties
        }
        
        if metadata_path:
            try:
                with Path(metadata_path).open("r") as f:
                    sub_crate_dict = json.load(f)
                
                sub_graph = sub_crate_dict.get("@graph", [])
                
                subcrate_root = None
                for idx, entity in enumerate(sub_graph):
                    if entity.get("@id") == "ro-crate-metadata.json":
                        about_ref = entity.get("about", {})
                        root_id = about_ref.get("@id") if isinstance(about_ref, dict) else about_ref
                        if root_id:
                            for e in sub_graph:
                                if e.get("@id") == root_id:
                                    subcrate_root = e
                                    break
                        break
                
                if subcrate_root:
                    if subcrate_root.get("version"):
                        dataset_args["version"] = subcrate_root.get("version")
                    if subcrate_root.get("license"):
                        dataset_args["license"] = subcrate_root.get("license")
                    if subcrate_root.get("keywords"):
                        dataset_args["keywords"] = parse_keywords_simple(subcrate_root.get("keywords"))
                    if subcrate_root.get("datePublished"):
                        date_str = subcrate_root.get("datePublished")
                        parsed_date = datetime.strptime(date_str, "%m/%d/%Y" if "/" in date_str else "%Y-%m-%d")
                        dataset_args["created_on"] = parsed_date
                        dataset_args["issued"] = parsed_date
                    if subcrate_root.get("publisher"):
                        dataset_args["publisher"] = subcrate_root.get("publisher")
                    if subcrate_root.get("identifier"):
                        dataset_args["doi"] = subcrate_root.get("identifier")
                    if subcrate_root.get("author"):
                        dataset_args["creators"] = parse_authors_from_ro_crate(subcrate_root.get("author"))
                    if subcrate_root.get("funder"):
                        dataset_args["funders"] = parse_funders_from_ro_crate(subcrate_root.get("funder"))
                    if subcrate_root.get("rai:dataUseCases"):
                        dataset_args["purposes"] = subcrate_root.get("rai:dataUseCases")
                    if subcrate_root.get("rai:dataLimitations"):
                        dataset_args["tasks"] = subcrate_root.get("rai:dataLimitations")
                    if subcrate_root.get("ethicalReview"):
                        dataset_args["ethical_reviews"] = subcrate_root.get("ethicalReview")
                    if subcrate_root.get("rai:dataReleaseMaintenancePlan"):
                        dataset_args["updates"] = subcrate_root.get("rai:dataReleaseMaintenancePlan")
                    if subcrate_root.get("rai:personalSensitiveInformation"):
                        dataset_args["sensitive_info"] = subcrate_root.get("rai:personalSensitiveInformation")
                    
                    addl_props = subcrate_root.get("additionalProperty")
                    if addl_props:
                        prohibited_uses = from_additional_property("Prohibited Uses")(addl_props)
                        if prohibited_uses:
                            dataset_args["discouraged_uses"] = prohibited_uses
                
                sub_rocrate = ROCrateV1_2.model_validate(sub_crate_dict)
                
                formats = set()
                for entity in sub_rocrate.metadataGraph:
                    entity_dict = entity.model_dump(by_alias=True)
                    entity_type = entity_dict.get("@type") or []
                    if isinstance(entity_type, str):
                        entity_type = [entity_type]
                    
                    if any(t in str(entity_type).lower() for t in ["dataset", "file"]):
                        fmt = entity_dict.get("fileFormat") or entity_dict.get("format")
                        if fmt:
                            formats.add(str(fmt))
                
                if formats:
                    for fmt in formats:
                        try:
                            dataset_args["format"] = FormatEnum(fmt)
                            break
                        except:
                            pass
            except Exception as e:
                print(f"Could not parse subcrate metadata: {e}")
        
        dataset_args = {k: v for k, v in dataset_args.items() if v is not None}
        
        try:
            datasets.append(Dataset(**dataset_args))
        except Exception as e:
            print(f"Error creating Dataset: {e}")
            print(f"Args: {dataset_args}")
    
    return datasets

D4D_DATASET_COLLECTION_MAPPING = {
    "id": {"source_key": "@id"},
    "title": {"source_key": "name"},
    "description": {"source_key": "description"},
    "version": {"source_key": "version"},
    "license": {"source_key": "license"},
    "keywords": {"source_key": "keywords", "parser": parse_keywords_simple},
    "created_on": {"source_key": "datePublished"},
    "issued": {"source_key": "datePublished"},
    "publisher": {"source_key": "publisher"},
    "doi": {"source_key": "identifier"},
    "download_url": {"source_key": "contentUrl"},
    "resources": {"builder_func": _build_datasets_from_subcrates},
}

MAPPING_CONFIGURATION = {
    "entity_map": {
        ("ROCrateMetadataElem", "ROOT"): {
            "target_class": DatasetCollection,
            "mapping_def": D4D_DATASET_COLLECTION_MAPPING
        },
        
        ("Dataset", "COMPONENT"): None,
        ("Schema", "COMPONENT"): None,
        ("Software", "COMPONENT"): None,
        ("Computation", "COMPONENT"): None,
    },

    "assembly_instructions": []
}