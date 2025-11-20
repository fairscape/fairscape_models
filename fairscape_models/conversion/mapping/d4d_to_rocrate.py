"""
D4D to ROCrate conversion mappings and utility functions.

This module provides the mapping configurations and parser functions needed
to convert D4D format data (Data for Development) to ROCrate format.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


# ============================================================================
# Parser Functions - Type Conversions
# ============================================================================

def _parse_datetime_to_iso(dt: Any) -> Optional[str]:
    """Convert datetime objects to ISO format strings."""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def _join_list_to_string(value: Any) -> Optional[str]:
    """Convert lists to comma-separated strings."""
    if value is None:
        return None
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v)
    return str(value)


def _parse_bytes_to_size_string(value: Any) -> Optional[str]:
    """Convert byte counts to human-readable size strings."""
    if value is None:
        return None
    if isinstance(value, str):
        return value

    bytes_val = int(value)
    if bytes_val >= 1024**4:
        return f"{bytes_val / (1024**4):.2f} TB"
    elif bytes_val >= 1024**3:
        return f"{bytes_val / (1024**3):.2f} GB"
    elif bytes_val >= 1024**2:
        return f"{bytes_val / (1024**2):.2f} MB"
    elif bytes_val >= 1024:
        return f"{bytes_val / 1024:.2f} KB"
    return f"{bytes_val} bytes"


def _format_enum_value(value: Any) -> Optional[str]:
    """Extract the value from enum objects."""
    if value is None:
        return None
    if hasattr(value, 'value'):
        return value.value
    return str(value)


# ============================================================================
# Parser Functions - Recursive String Extraction
# ============================================================================

def _extract_strings_recursively(value: Any) -> List[str]:
    """
    Recursively extract all string values from nested structures.

    Handles dictionaries, lists, and primitive values, looking for specific
    keys like 'description', 'response', etc.
    """
    strings = []

    if value is None:
        return strings

    if isinstance(value, str):
        return [value.strip()] if value.strip() else []

    if isinstance(value, dict):
        # Look for specific keys first
        for key in ['description', 'response', 'identification', 'distribution',
                    'was_directly_observed', 'was_reported_by_subjects',
                    'was_inferred_derived', 'was_validated_verified']:
            if key in value:
                strings.extend(_extract_strings_recursively(value[key]))

        # If no specific keys found, extract from all values
        if not strings:
            for v in value.values():
                strings.extend(_extract_strings_recursively(v))

    elif isinstance(value, list):
        for item in value:
            strings.extend(_extract_strings_recursively(item))

    else:
        s = str(value).strip()
        if s:
            strings.append(s)

    return strings


def _flatten_to_string(value: Any) -> Optional[str]:
    """Flatten nested structures to a single space-separated string."""
    if value is None:
        return None

    strings = _extract_strings_recursively(value)
    return " ".join(strings) if strings else None


def _flatten_to_list(value: Any) -> Optional[List[str]]:
    """Flatten nested structures to a list of strings."""
    if value is None:
        return None

    strings = _extract_strings_recursively(value)
    return strings if strings else None


# ============================================================================
# Builder Functions - Combine Multiple Fields
# ============================================================================

def _combine_license_terms(source_dict: Dict[str, Any]) -> Optional[str]:
    """Combine license-related fields into a single string."""
    parts = []
    for key in ["license_and_use_terms", "ip_restrictions", "regulatory_restrictions"]:
        if source_dict.get(key):
            extracted = _flatten_to_string(source_dict[key])
            if extracted:
                parts.append(extracted)
    return " | ".join(parts) if parts else None


def _combine_limitations(source_dict: Dict[str, Any]) -> Optional[str]:
    """Combine limitation-related fields."""
    items = []
    for key in ["discouraged_uses", "errata", "content_warnings"]:
        if source_dict.get(key):
            extracted = _flatten_to_string(source_dict[key])
            if extracted:
                items.append(extracted)
    return " ".join(items) if items else None


def _combine_biases(source_dict: Dict[str, Any]) -> Optional[str]:
    """Combine bias-related fields."""
    items = []
    for key in ["anomalies", "subpopulations"]:
        if source_dict.get(key):
            extracted = _flatten_to_string(source_dict[key])
            if extracted:
                items.append(extracted)
    return "; ".join(items) if items else None


def _combine_use_cases(source_dict: Dict[str, Any]) -> Optional[str]:
    """Combine use case-related fields."""
    items = []
    for key in ["purposes", "tasks", "existing_uses", "other_tasks"]:
        if source_dict.get(key):
            extracted = _flatten_to_string(source_dict[key])
            if extracted:
                items.append(extracted)
    return " ".join(items) if items else None


def _combine_maintenance(source_dict: Dict[str, Any]) -> Optional[str]:
    """Combine maintenance-related fields with labels."""
    parts = []
    if source_dict.get("maintainers"):
        extracted = _flatten_to_string(source_dict["maintainers"])
        if extracted:
            parts.append(f"Maintainers: {extracted}")
    if source_dict.get("updates"):
        extracted = _flatten_to_string(source_dict["updates"])
        if extracted:
            parts.append(f"Updates: {extracted}")
    if source_dict.get("retention_limit"):
        extracted = _flatten_to_string(source_dict["retention_limit"])
        if extracted:
            parts.append(f"Retention: {extracted}")
    return " | ".join(parts) if parts else None


def _combine_collection_info(source_dict: Dict[str, Any]) -> Optional[str]:
    """Combine data collection information."""
    items = []
    if source_dict.get("acquisition_methods"):
        extracted = _flatten_to_string(source_dict["acquisition_methods"])
        if extracted:
            items.append(extracted)
    if source_dict.get("instances"):
        instances = source_dict["instances"]
        if isinstance(instances, list):
            items.append(f"{len(instances)} instances")
        else:
            items.append("Instances documented")
    return " ".join(items) if items else None


def _combine_collection_mechanisms(source_dict: Dict[str, Any]) -> List[str]:
    """Extract collection mechanisms as a list."""
    items = []
    if source_dict.get("collection_mechanisms"):
        extracted = _flatten_to_list(source_dict["collection_mechanisms"])
        if extracted:
            items.extend(extracted)
    return items if items else None


def _combine_sensitive_info(source_dict: Dict[str, Any]) -> List[str]:
    """Combine sensitive information fields."""
    items = []
    for key in ["confidential_elements", "sensitive_elements"]:
        if source_dict.get(key):
            extracted = _flatten_to_list(source_dict[key])
            if extracted:
                items.extend(extracted)
    if source_dict.get("is_deidentified"):
        deident = _flatten_to_string(source_dict["is_deidentified"])
        if deident:
            items.append(f"Deidentified: {deident}")
    return items if items else None


def _combine_social_impact(source_dict: Dict[str, Any]) -> Optional[str]:
    """Combine social impact-related fields."""
    items = []
    for key in ["future_use_impacts", "data_protection_impacts"]:
        if source_dict.get(key):
            extracted = _flatten_to_string(source_dict[key])
            if extracted:
                items.append(extracted)
    return " ".join(items) if items else None


# ============================================================================
# Mapping Configurations
# ============================================================================

DATASET_COLLECTION_TO_RELEASE_MAPPING = {
    # Core metadata
    "@id": {"source_key": "id"},
    "name": {"source_key": "title"},
    "description": {"source_key": "description"},
    "author": {"source_key": "creators", "parser": _join_list_to_string},
    "version": {"source_key": "version"},
    "license": {"source_key": "license"},
    "keywords": {"source_key": "keywords"},
    "identifier": {"source_key": "doi"},
    "publisher": {"source_key": "publisher"},

    # Dates
    "datePublished": {"source_key": "issued", "parser": _parse_datetime_to_iso},
    "dateCreated": {"source_key": "created_on", "parser": _parse_datetime_to_iso},
    "dateModified": {"source_key": "last_updated_on", "parser": _parse_datetime_to_iso},

    # Links and content
    "url": {"source_key": "page"},
    "contentUrl": {"source_key": "download_url"},
    "encodingFormat": {"source_key": "encoding", "parser": _format_enum_value},
    "contentSize": {"source_key": "bytes", "parser": _parse_bytes_to_size_string},
    "conditionsOfAccess": {"builder_func": _combine_license_terms},
    "conformsTo": {"source_key": "conforms_to"},

    # RAI (Responsible AI) properties
    "rai:dataLimitations": {"builder_func": _combine_limitations},
    "rai:dataBiases": {"builder_func": _combine_biases},
    "rai:dataUseCases": {"builder_func": _combine_use_cases},
    "rai:dataReleaseMaintenancePlan": {"builder_func": _combine_maintenance},
    "rai:dataCollection": {"builder_func": _combine_collection_info},
    "rai:dataCollectionType": {"builder_func": _combine_collection_mechanisms},
    "rai:dataCollectionRawData": {"source_key": "raw_sources", "parser": _flatten_to_string},
    "rai:dataManipulationProtocol": {"source_key": "cleaning_strategies", "parser": _flatten_to_string},
    "rai:dataPreprocessingProtocol": {"source_key": "preprocessing_strategies", "parser": _flatten_to_string},
    "rai:dataAnnotationProtocol": {"source_key": "labeling_strategies", "parser": _flatten_to_string},
    "rai:personalSensitiveInformation": {"builder_func": _combine_sensitive_info},
    "rai:dataSocialImpact": {"builder_func": _combine_social_impact},

    # Additional metadata
    "funder": {"source_key": "funders", "parser": _flatten_to_string},
    "ethicalReview": {"source_key": "ethical_reviews", "parser": _flatten_to_string},
}


DATASET_TO_SUBCRATE_MAPPING = {
    # Core metadata
    "@id": {"source_key": "id"},
    "name": {"source_key": "title"},
    "description": {"source_key": "description"},
    "author": {"source_key": "creators", "parser": _join_list_to_string},
    "version": {"source_key": "version"},
    "license": {"source_key": "license"},
    "keywords": {"source_key": "keywords"},
    "identifier": {"source_key": "doi"},
    "publisher": {"source_key": "publisher"},

    # Dates
    "datePublished": {"source_key": "issued", "parser": _parse_datetime_to_iso},
    "dateCreated": {"source_key": "created_on", "parser": _parse_datetime_to_iso},
    "dateModified": {"source_key": "last_updated_on", "parser": _parse_datetime_to_iso},

    # Links and content
    "url": {"source_key": "page"},
    "contentUrl": {"source_key": "download_url"},
    "encodingFormat": {"source_key": "encoding", "parser": _format_enum_value},
    "fileFormat": {"source_key": "format", "parser": _format_enum_value},
    "contentSize": {"source_key": "bytes", "parser": _parse_bytes_to_size_string},

    # Checksums
    "md5": {"source_key": "md5"},
    "sha256": {"source_key": "sha256"},

    # Access and conformance
    "conditionsOfAccess": {"builder_func": _combine_license_terms},
    "conformsTo": {"source_key": "conforms_to"},

    # RAI (Responsible AI) properties
    "rai:dataLimitations": {"builder_func": _combine_limitations},
    "rai:dataBiases": {"builder_func": _combine_biases},
    "rai:dataUseCases": {"builder_func": _combine_use_cases},
    "rai:dataReleaseMaintenancePlan": {"builder_func": _combine_maintenance},
    "rai:dataCollection": {"builder_func": _combine_collection_info},
    "rai:dataCollectionType": {"builder_func": _combine_collection_mechanisms},
    "rai:dataCollectionRawData": {"source_key": "raw_sources", "parser": _flatten_to_string},
    "rai:dataManipulationProtocol": {"source_key": "cleaning_strategies", "parser": _flatten_to_string},
    "rai:dataPreprocessingProtocol": {"source_key": "preprocessing_strategies", "parser": _flatten_to_string},
    "rai:dataAnnotationProtocol": {"source_key": "labeling_strategies", "parser": _flatten_to_string},
    "rai:personalSensitiveInformation": {"builder_func": _combine_sensitive_info},
    "rai:dataSocialImpact": {"builder_func": _combine_social_impact},

    # Additional metadata
    "funder": {"source_key": "funders", "parser": _flatten_to_string},
    "ethicalReview": {"source_key": "ethical_reviews", "parser": _flatten_to_string},
}
