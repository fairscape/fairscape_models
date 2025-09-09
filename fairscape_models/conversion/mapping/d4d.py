import re
from typing import List, Dict, Any, Optional

# data_sheets_schema.py in current directory
from data_sheets_schema import DatasetCollection, Dataset

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

D4D_INFORMATION_MAPPING = {
    "id":                  {"source_key": "@id"},
    "title":               {"source_key": "name"},
    "description":         {"source_key": "description"},
    "version":             {"source_key": "version"},
    "license":             {"source_key": "license"},
    "keywords":            {"source_key": "keywords", "parser": parse_keywords_simple},
    "created_on":          {"source_key": "datePublished"},
    "issued":              {"source_key": "datePublished"}, 
    "publisher":           {"source_key": "publisher"},
    "doi":                 {"source_key": "identifier"},
    "download_url":        {"source_key": "contentUrl"},
    "related_publications":{"source_key": "associatedPublication", "parser": parse_related_publications},
}

D4D_DATASET_COLLECTION_MAPPING = {
    **D4D_INFORMATION_MAPPING,
}

D4D_DATASET_MAPPING = {
    **D4D_INFORMATION_MAPPING,
    "bytes":               {"source_key": "contentSize", "parser": parse_file_size_to_bytes},
    "format":              {"source_key": "fileFormat"},
    "md5":                 {"source_key": "md5"},
    "path":                {"source_key": "contentUrl"},
    "creators":            {"source_key": "author", "parser": parse_authors_from_ro_crate},
    "funders":             {"source_key": "funder", "parser": parse_funders_from_ro_crate},

    "purposes":            {"source_key": "additionalProperty", "parser": from_additional_property("Intended Use")},
    "tasks":               {"source_key": "additionalProperty", "parser": from_additional_property("Intended Use")},
    "ethical_reviews":     {"source_key": "additionalProperty", "parser": from_additional_property("Ethical Review")},
    "discouraged_uses":    {"source_key": "additionalProperty", "parser": from_additional_property("Prohibited Uses")},
    "updates":             {"source_key": "additionalProperty", "parser": from_additional_property("Maintenance Plan")},
}

MAPPING_CONFIGURATION = {
    "entity_map": {
        ("ROCrateMetadataElem", "ROOT"): {
            "target_class": DatasetCollection,
            "mapping_def": D4D_DATASET_COLLECTION_MAPPING
        },
        
        ("Dataset", "PART"): {
            "target_class": Dataset,
            "mapping_def": D4D_DATASET_MAPPING
        },
    },

    "assembly_instructions": [
        {
            "child_type": Dataset,
            "child_attribute_to_link": "id",
            "parent_attribute": "resources",
            "parent_type": DatasetCollection
        }
    ]
}