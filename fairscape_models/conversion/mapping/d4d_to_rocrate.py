"""
D4D to ROCrate conversion mappings and utility functions.

This module provides the mapping configurations and parser functions needed
to convert D4D pydantic classes to ROCrate v1.2.
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


def _combine_social_impact(source_dict: Dict[str, Any]) -> Optional[str]:
    """Combine social impact-related fields."""
    items = []
    for key in ["future_use_impacts", "data_protection_impacts"]:
        if source_dict.get(key):
            extracted = _flatten_to_string(source_dict[key])
            if extracted:
                items.append(extracted)
    return " ".join(items) if items else None


def _extract_missing_data(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract missing data information from instances and documentation."""
    items = []
    # Extract from missing_data_documentation at dataset level
    if source_dict.get("missing_data_documentation"):
        extracted = _flatten_to_string(source_dict["missing_data_documentation"])
        if extracted:
            items.append(extracted)
    # Extract missing_information from instances
    if source_dict.get("instances"):
        instances = source_dict["instances"]
        if isinstance(instances, list):
            for inst in instances:
                if isinstance(inst, dict) and inst.get("missing_information"):
                    extracted = _flatten_to_string(inst["missing_information"])
                    if extracted:
                        items.append(extracted)
    return " ".join(items) if items else None


def _extract_annotations_per_item(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract annotations_per_item from labeling strategies."""
    items = []
    if source_dict.get("labeling_strategies"):
        strategies = source_dict["labeling_strategies"]
        if isinstance(strategies, list):
            for strategy in strategies:
                if isinstance(strategy, dict) and strategy.get("annotations_per_item"):
                    items.append(str(strategy.get("annotations_per_item")))
        elif isinstance(strategies, dict) and strategies.get("annotations_per_item"):
            items.append(str(strategies.get("annotations_per_item")))
    return ", ".join(items) if items else None

def _extract_annotations_platform(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract annotations_platform from labeling strategies."""
    items = []
    if source_dict.get("labeling_strategies"):
        strategies = source_dict["labeling_strategies"]
        if isinstance(strategies, list):
            for strategy in strategies:
                if isinstance(strategy, dict) and strategy.get("data_annotation_platform"):
                    items.append(str(strategy.get("data_annotation_platform")))
        elif isinstance(strategies, dict) and strategies.get("data_annotation_platform"):
            items.append(str(strategies.get("data_annotation_platform")))
    return ", ".join(items) if items else None


def _extract_confidentiality_level(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract confidentiality level from regulatory restrictions."""
    if source_dict.get("regulatory_restrictions"):
        restrictions = source_dict["regulatory_restrictions"]
        if isinstance(restrictions, dict):
            level = restrictions.get("confidentiality_level")
            if level:
                return _format_enum_value(level)
        elif isinstance(restrictions, list):
            for r in restrictions:
                if isinstance(r, dict) and r.get("confidentiality_level"):
                    return _format_enum_value(r.get("confidentiality_level"))
    return None


def _extract_governance_committee(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract governance committee contact from regulatory restrictions."""
    if source_dict.get("regulatory_restrictions"):
        restrictions = source_dict["regulatory_restrictions"]
        if isinstance(restrictions, dict):
            return restrictions.get("governance_committee_contact")
        elif isinstance(restrictions, list):
            for r in restrictions:
                if isinstance(r, dict) and r.get("governance_committee_contact"):
                    return r.get("governance_committee_contact")
    return None


def _extract_principal_investigator(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract principal investigators from creators where principal_investigator=True."""
    pi_names = []
    if source_dict.get("creators"):
        creators = source_dict["creators"]
        if isinstance(creators, list):
            for creator in creators:
                if isinstance(creator, dict):
                    if creator.get("principal_investigator"):
                        person = creator.get("person")
                        if isinstance(person, dict):
                            name = person.get("name") or person.get("id")
                            if name:
                                pi_names.append(str(name))
                        elif isinstance(person, str):
                            pi_names.append(person)
                        elif creator.get("name"):
                            pi_names.append(str(creator.get("name")))
                        elif creator.get("id"):
                            pi_names.append(str(creator.get("id")))
    return ", ".join(pi_names) if pi_names else None


def _extract_contact_email(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract contact email from ethical reviews contact_person."""
    if source_dict.get("ethical_reviews"):
        reviews = source_dict["ethical_reviews"]
        if isinstance(reviews, list):
            for review in reviews:
                if isinstance(review, dict):
                    contact = review.get("contact_person")
                    if isinstance(contact, dict) and contact.get("email"):
                        return contact.get("email")
                    elif isinstance(contact, str):
                        # It's just an ID/string reference
                        return contact
        elif isinstance(reviews, dict):
            contact = reviews.get("contact_person")
            if isinstance(contact, dict) and contact.get("email"):
                return contact.get("email")
            elif isinstance(contact, str):
                return contact
    return None


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

    # RAI (Responsible AI) properties - Data Lifecycle
    "rai:dataLimitations": {"source_key": "known_limitations", "parser": _flatten_to_string},
    "rai:dataCollection": {"source_key": "collection_mechanisms", "parser": _flatten_to_string},
    "rai:dataCollectionType": {"source_key": "collection_mechanisms", "parser": _flatten_to_string},
    "rai:dataCollectionMissingData": {"builder_func": _extract_missing_data},
    "rai:dataCollectionRawData": {"source_key": "raw_data_sources", "parser": _flatten_to_string},
    "rai:dataCollectionTimeframe": {"source_key": "collection_timeframes", "parser": _flatten_to_string},
    "rai:dataPreprocessingProtocol": {"source_key": "preprocessing_strategies", "parser": _flatten_to_list},

    # RAI - Data Labeling
    "rai:dataAnnotationProtocol": {"source_key": "labeling_strategies", "parser": _flatten_to_string},
    "rai:dataAnnotationPlatform": {"builder_func": _extract_annotations_platform},  
    "rai:dataAnnotationProtocol": {"source_key": "annotation_analysis", "parser": _flatten_to_string},
    "rai:annotationsPerItem": {"builder_func": _extract_annotations_per_item},
    "rai:machineAnnotationTools": {"source_key": "machine_annotation_tools", "parser": _flatten_to_string},

    # RAI - Safety & Fairness
    "rai:dataBiases": {"source_key": "known_biases", "parser": _flatten_to_string},
    "rai:dataSocialImpact": {"builder_func": _combine_social_impact},
    "rai:personalSensitiveInformation":  {"source_key": "sensitive_elements", "parser": _flatten_to_string}, 
    "rai:dataUseCases": {"source_key": "intended_uses", "parser": _flatten_to_string}, 

    # RAI - Compliance & Governance
    "rai:dataManipulationProtocol": {"source_key": "cleaning_strategies", "parser": _flatten_to_string},
    "rai:dataImputationProtocol": {"source_key": "imputation_method", "parser": _flatten_to_string},
    "rai:dataReleaseMaintenancePlan": {"source_key": "update_plan", "parser": _flatten_to_string},

    # Additional metadata
    "funder": {"source_key": "funders", "parser": _flatten_to_string},
    "ethicalReview": {"source_key": "ethical_reviews", "parser": _flatten_to_string},
    "citation": {"source_key": "citation"},
    "principalInvestigator": {"builder_func": _extract_principal_investigator},
    "contactEmail": {"builder_func": _extract_contact_email},
    "confidentialityLevel": {"builder_func": _extract_confidentiality_level},
    "humanSubject": {"source_key": "human_subject_research", "parser": _flatten_to_string},
    "governanceCommittee": {"builder_func": _extract_governance_committee},
    "prohibitedUses": {"source_key": "discouraged_uses", "parser": _flatten_to_string},
    "evi:formats": {"source_key": "distribution_formats", "parser": _flatten_to_string},
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
    "contentSize": {"source_key": "bytes", "parser": _parse_bytes_to_size_string},
    "conditionsOfAccess": {"builder_func": _combine_license_terms},
    "conformsTo": {"source_key": "conforms_to"},

    # RAI (Responsible AI) properties - Data Lifecycle
    "rai:dataLimitations": {"source_key": "known_limitations", "parser": _flatten_to_string},
    "rai:dataCollection": {"source_key": "collection_mechanisms", "parser": _flatten_to_string},
    "rai:dataCollectionType": {"source_key": "collection_mechanisms", "parser": _flatten_to_string},
    "rai:dataCollectionMissingData": {"builder_func": _extract_missing_data},
    "rai:dataCollectionRawData": {"source_key": "raw_sources", "parser": _flatten_to_string},
    "rai:dataCollectionTimeframe": {"source_key": "collection_timeframes", "parser": _flatten_to_string},
    "rai:dataPreprocessingProtocol": {"source_key": "preprocessing_strategies", "parser": _flatten_to_list},

    # RAI - Data Labeling
    "rai:dataAnnotationProtocol": {"source_key": "labeling_strategies", "parser": _flatten_to_string},
    "rai:dataAnnotationPlatform": {"builder_func": _extract_annotations_platform},  
    "rai:dataAnnotationProtocol": {"source_key": "annotation_analysis", "parser": _flatten_to_string},
    "rai:annotationsPerItem": {"builder_func": _extract_annotations_per_item},
    "rai:machineAnnotationTools": {"source_key": "machine_annotation_tools", "parser": _flatten_to_string},

    # RAI - Safety & Fairness
    "rai:dataBiases": {"source_key": "known_biases", "parser": _flatten_to_string},
    "rai:dataSocialImpact": {"builder_func": _combine_social_impact},
    "rai:personalSensitiveInformation":  {"source_key": "sensitive_elements", "parser": _flatten_to_string}, 
    "rai:dataUseCases": {"source_key": "intended_uses", "parser": _flatten_to_string}, 

    # RAI - Compliance & Governance
    "rai:dataManipulationProtocol": {"source_key": "cleaning_strategies", "parser": _flatten_to_string},
    "rai:dataImputationProtocol": {"source_key": "imputation_method", "parser": _flatten_to_string},
    "rai:dataReleaseMaintenancePlan": {"source_key": "update_plan", "parser": _flatten_to_string},

    # Additional metadata
    "funder": {"source_key": "funders", "parser": _flatten_to_string},
    "ethicalReview": {"source_key": "ethical_reviews", "parser": _flatten_to_string},
    "citation": {"source_key": "citation"},
    "principalInvestigator": {"builder_func": _extract_principal_investigator},
    "contactEmail": {"builder_func": _extract_contact_email},
    "confidentialityLevel": {"builder_func": _extract_confidentiality_level},
    "humanSubject": {"source_key": "human_subject_research", "parser": _flatten_to_string},
    "governanceCommittee": {"builder_func": _extract_governance_committee},
    "prohibitedUses": {"source_key": "discouraged_uses", "parser": _flatten_to_string},
    "evi:formats": {"source_key": "distribution_formats", "parser": _flatten_to_string},
}