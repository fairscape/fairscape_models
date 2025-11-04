from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
from functools import partial

from fairscape_models.rocrate import ROCrateV1_2, Dataset as ROCrateDataset, Schema as ROCrateSchema
from fairscape_models.conversion.models import (
    CroissantDataset, CroissantFileObject, CroissantRecordSet, CroissantField,
    CroissantSource, CroissantIdentifier, DEFAULT_CROISSANT_CONTEXT
)
import fairscape_models.conversion.mapping.utils as conversion_utils
from fairscape_models.conversion.converter import ROCToTargetConverter

class EncodingFormat:
    CSV = "text/csv"
    GIT = "git+https"
    JSON = "application/json"
    JSON_LINES = "application/jsonlines"
    PARQUET = "application/x-parquet"
    TEXT = "text/plain"
    TSV = "text/tsv"
    TAR = "application/x-tar"
    ZIP = "application/zip"


CROISSANT_SPLIT_RECORDSET = {
    "@id": "splits",
    "@type": "cr:RecordSet",
    "name": "splits",
    "dataType": "cr:Split",
    "description": "Maps split names to semantic values.",
    "key": "splits/name",
    "field": [
        {
            "@type": "cr:Field",
            "@id": "splits/name",
            "name": "splits/name",
            "description": "One of: train, val, test.",
            "dataType": "sc:Text"
        },
        {
            "@type": "cr:Field",
            "@id": "splits/url",
            "name": "splits/url",
            "description": "Corresponding mlcommons.org definition URL",
             "dataType": [
            "sc:URL",
            "wd:Q3985153"
          ]
        }
    ],
    "data": [
        {
            "splits/name": "train",
            "splits/url": "https://mlcommons.org/definitions/training_split"
        },
        {
            "splits/name": "val",
            "splits/url": "https://mlcommons.org/definitions/validation_split"
        },
        {
            "splits/name": "test",
            "splits/url": "https://mlcommons.org/definitions/test_split"
        }
    ]
}


def map_format_to_mime_type(format_str: Optional[str]) -> str:
    if not format_str:
        return EncodingFormat.TEXT
    
    format_lower = format_str.lower()
    
    if format_lower in ['csv', '.csv']:
        return EncodingFormat.CSV
    elif format_lower in ['json', '.json']:
        return EncodingFormat.JSON
    elif format_lower in ['jsonl', '.jsonl', 'jsonlines', '.jsonlines']:
        return EncodingFormat.JSON_LINES
    elif format_lower in ['parquet', '.parquet']:
        return EncodingFormat.PARQUET
    elif format_lower in ['txt', '.txt', 'text', 'plain']:
        return EncodingFormat.TEXT
    elif format_lower in ['tsv', '.tsv']:
        return EncodingFormat.TSV
    elif format_lower in ['tar', '.tar']:
        return EncodingFormat.TAR
    elif format_lower in ['zip', '.zip']:
        return EncodingFormat.ZIP
    elif format_lower.startswith('git'):
        return EncodingFormat.GIT
    else:
        return EncodingFormat.TEXT


def _get_additional_prop_values(
    prop_list: Optional[List[Dict]], names_to_find: Union[str, List[str]]
) -> Optional[List[str]]:
    if not prop_list:
        return None
    if isinstance(names_to_find, str):
        names_to_find = [names_to_find]
    
    values = []
    for name in names_to_find:
        found_values = [p.get('value') for p in prop_list if p.get('name') == name and p.get('value')]
        values.extend(found_values)
        
    return values if values else None


def _parse_personal_sensitive_info(prop_list: Optional[List[Dict]]) -> Optional[List[str]]:
    if not prop_list:
        return None
    human = next((p.get('value') for p in prop_list if p.get('name') == 'Human Subject'), None)
    deidentified = next((p.get('value') for p in prop_list if p.get('name') == 'De-identified Samples'), None)
    parts = []
    if human is not None:
        parts.append(f"Involves human subjects: {human}.")
    if deidentified is not None:
        parts.append(f"Uses de-identified samples: {deidentified}.")
    return [" ".join(parts)] if parts else None


def _build_rai_property(
    converter_instance: 'ROCToTargetConverter',
    source_entity_model: BaseModel,
    rai_key: str,
    additional_prop_name: Union[str, List[str]],
    is_list: bool = True
) -> Optional[Union[str, List[str]]]:
    source_dict = source_entity_model.model_dump(by_alias=True)

    if rai_key in source_dict and source_dict[rai_key] is not None:
        value = source_dict[rai_key]
        if is_list and not isinstance(value, list):
            return [value]
        return value

    prop_list = source_dict.get("additionalProperty")
    if prop_list and additional_prop_name:
        values = _get_additional_prop_values(prop_list, additional_prop_name)
        if values:
            return values if is_list else values[0]

    return None


def _build_personal_sensitive_info(
    converter_instance: 'ROCToTargetConverter', source_entity_model: BaseModel
) -> Optional[List[str]]:
    source_dict = source_entity_model.model_dump(by_alias=True)
    
    rai_key = "rai:personalSensitiveInformation"
    if rai_key in source_dict and source_dict[rai_key] is not None:
        value = source_dict[rai_key]
        return value if isinstance(value, list) else [value]
        
    return _parse_personal_sensitive_info(source_dict.get("additionalProperty"))


def _create_fields_recursively(
    converter_instance: 'ROCToTargetConverter',
    properties: Dict[str, Any],
    field_mapping_def: Dict[str, Any],
    record_set_id: str,
    file_object_id: str,
    parent_path: str = ""
):
    fields = []
    has_split_field = False
    
    for prop_name, prop_details in properties.items():
        field_dict = converter_instance._map_single_object_from_dict(prop_details, field_mapping_def)
        
        full_path = f"{parent_path}/{prop_name}" if parent_path else prop_name
        sanitized_path = full_path.replace(' ', '_').replace('-', '_')
        field_id = f"{record_set_id}/{sanitized_path}"
        
        field_dict["@id"] = field_id
        field_dict["name"] = conversion_utils.format_name(prop_name)
        field_dict["source"] = {
            "fileObject": {"@id": file_object_id},
            "extract": {"column": f"{full_path.replace('/', '.')}"}
        }

        if prop_name.lower() == "split":
            has_split_field = True
            field_dict["dataType"] = ["sc:Text", "wd:Q3985153"]
            field_dict["references"] = {"field": {"@id": "splits/name"}}

        if prop_details.get("type") == "object" and "properties" in prop_details and prop_details["properties"]:
            field_dict["dataType"] = "sc:Thing"
            nested_properties = prop_details["properties"]
            sub_fields, nested_has_split = _create_fields_recursively(
                converter_instance,
                nested_properties,
                field_mapping_def,
                record_set_id,
                file_object_id,
                parent_path=full_path
            )
            if nested_has_split:
                has_split_field = True
            if sub_fields:
                field_dict["subField"] = sub_fields
        
        if prop_details.get("separator"):
             field_dict["repeated"] = True
             field_dict["separator"] = prop_details["separator"]

        fields.append(CroissantField.model_validate(field_dict))
    
    return fields, has_split_field


def build_croissant_record_sets(
    converter_instance: 'ROCToTargetConverter',
    source_entity_model: BaseModel
) -> List[CroissantRecordSet]:
    record_sets = []
    has_any_split_field = False
    source_rocrate = converter_instance.source_crate
    all_target_objects = converter_instance.target_objects_cache
    field_mapping_def = converter_instance.mapping_config.get("sub_mappings", {}).get("field_mapping")
    
    if not field_mapping_def: return []

    schemas = source_rocrate.getSchemas()
    datasets = source_rocrate.getDatasets()
    schema_to_dataset_map: Dict[str, ROCrateDataset] = {
        ds.dataSchema.guid: ds for ds in datasets if ds.dataSchema and ds.dataSchema.guid
    }

    for schema in schemas:
        if schema.guid not in schema_to_dataset_map: continue
        
        source_dataset = schema_to_dataset_map[schema.guid]
        target_file_object = all_target_objects.get(source_dataset.guid)
        if not target_file_object or not isinstance(target_file_object, CroissantFileObject): continue
        
        record_set_id = conversion_utils.ro_crate_id_to_croissant_local_id(schema.guid, prefix="recordset-")

        croissant_fields, has_split = _create_fields_recursively(
            converter_instance,
            {k: v.model_dump(by_alias=True) for k, v in schema.properties.items()}, 
            field_mapping_def,
            record_set_id=record_set_id,
            file_object_id=target_file_object.id
        )

        if has_split:
            has_any_split_field = True

        if not croissant_fields: continue

        record_sets.append(CroissantRecordSet.model_validate({
            "@id": record_set_id,
            "name": conversion_utils.format_name(schema.name),
            "description": schema.description,
            "field": croissant_fields,
            "key": [f"{record_set_id}/{conversion_utils.format_name(req)}" for req in schema.required] if schema.required else None
        }))
    
    if has_any_split_field:
        record_sets.append(CroissantRecordSet.model_validate(CROISSANT_SPLIT_RECORDSET))
        
    return record_sets


CROISSANT_DATASET_MAPPING = {
    "context":        {"fixed_value": DEFAULT_CROISSANT_CONTEXT},
    "@type":          {"fixed_value": "sc:Dataset"},
    "dct:conformsTo": {"fixed_value": "http://mlcommons.org/croissant/RAI/1.0"},
    "name":           {"source_key": "name", "parser": conversion_utils.format_name},
    "description":    {"source_key": "description"},
    "license":        {"source_key": "license"},
    "citeAs":         {"source_key": "associatedPublication", "parser": conversion_utils.parse_cite_as},
    "url":            {"source_key": "url"},
    "keywords":       {"source_key": "keywords"},
    "version":        {"source_key": "version"},
    "creator":        {"source_key": "author", "parser": conversion_utils.parse_authors_to_person_list},
    "publisher":      {"source_key": "publisher", "parser": conversion_utils.parse_publisher},
    
    "distribution":   {"builder_func": None},
    "recordSet":      {"builder_func": build_croissant_record_sets},
    
    "rai:dataCollection": {"source_key": "rai:dataCollection"},
    "rai:dataCollectionType": {"source_key": "rai:dataCollectionType"},
    "rai:dataCollectionMissingData": {"source_key": "rai:dataCollectionMissingData"},
    "rai:dataCollectionRawData": {"source_key": "rai:dataCollectionRawData"},
    "rai:dataCollectionTimeframe": {"source_key": "rai:dataCollectionTimeframe"},
    "rai:dataImputationProtocol": {"source_key": "rai:dataImputationProtocol"},
    "rai:dataManipulationProtocol": {"source_key": "rai:dataManipulationProtocol"},
    "rai:dataPreprocessingProtocol": {"source_key": "rai:dataPreprocessingProtocol"},
    "rai:dataAnnotationProtocol": {"source_key": "rai:dataAnnotationProtocol"},
    "rai:dataAnnotationPlatform": {"source_key": "rai:dataAnnotationPlatform"},
    "rai:dataAnnotationAnalysis": {"source_key": "rai:dataAnnotationAnalysis"},
    "rai:socialImpact": {"source_key": "rai:socialImpact"},

    "rai:dataUseCases": {
        "builder_func": partial(_build_rai_property, rai_key="rai:dataUseCases", additional_prop_name="Intended Use")
    },
    "rai:dataLimitations": {
        "builder_func": partial(_build_rai_property, rai_key="rai:dataLimitations", additional_prop_name=["Limitations", "Prohibited Uses"])
    },
    "rai:dataBiases": {
        "builder_func": partial(_build_rai_property, rai_key="rai:dataBiases", additional_prop_name="Potential Sources of Bias")
    },
    "rai:personalSensitiveInformation": {
        "builder_func": _build_personal_sensitive_info
    },
    "rai:dataReleaseMaintenancePlan": {
        "builder_func": partial(_build_rai_property, rai_key="rai:dataReleaseMaintenancePlan", additional_prop_name="Maintenance Plan")
    },
}

CROISSANT_FILE_OBJECT_MAPPING = {
    "@id":            {"source_key": "@id", "parser": lambda x: conversion_utils.ro_crate_id_to_croissant_local_id(x, prefix="file-")},
    "@type":          {"fixed_value": "cr:FileObject"},
    "name":           {"source_key": "name", "parser": conversion_utils.format_name},
    "description":    {"source_key": "description"},
    "contentUrl":     {"source_key": "contentUrl"},
    "encodingFormat": {"source_key": "format", "parser": map_format_to_mime_type},
    "sha256":         {"source_key": "sha256"},
    "md5":            {"source_key": "md5", "parser": conversion_utils.format_md5},
}

CROISSANT_FIELD_MAPPING = {
    "@type":       {"fixed_value": "cr:Field"},
    "description": {"source_key": "description"},
    "dataType":    {"source_key": "type", "parser": conversion_utils.map_schema_type_to_croissant_data_type},
}


MAPPING_CONFIGURATION = {
    "entity_map": {
        ("ROCrateMetadataElem", "ROOT"): {
            "target_class": CroissantDataset, "mapping_def": CROISSANT_DATASET_MAPPING
        },
        ("Dataset", "COMPONENT"): {
            "target_class": CroissantFileObject, "mapping_def": CROISSANT_FILE_OBJECT_MAPPING
        },
        ("Schema", "COMPONENT"): None,
    },
    "sub_mappings": {
        "field_mapping": CROISSANT_FIELD_MAPPING
    },
    "assembly_instructions": [
        {
            "child_type": CroissantFileObject,
            "parent_attribute": "distribution",
            "parent_type": CroissantDataset
        }
    ]
}