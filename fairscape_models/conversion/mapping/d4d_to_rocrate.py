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


def _extract_collection_timeframe(source_dict: Dict[str, Any]) -> Optional[List[str]]:
    """Extract collection timeframe information."""
    if source_dict.get("collection_timeframes"):
        return _flatten_to_list(source_dict["collection_timeframes"])
    return None


def _extract_imputation_protocol(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract imputation protocol information."""
    if source_dict.get("imputation_protocols"):
        return _flatten_to_string(source_dict["imputation_protocols"])
    return None


def _extract_annotation_analysis(source_dict: Dict[str, Any]) -> Optional[List[str]]:
    """Extract annotation analysis information."""
    if source_dict.get("annotation_analyses"):
        return _flatten_to_list(source_dict["annotation_analyses"])
    return None


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


def _extract_human_subject(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract human subject research information."""
    if source_dict.get("human_subject_research"):
        return _flatten_to_string(source_dict["human_subject_research"])
    return None


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


def _extract_prohibited_uses(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract prohibited/discouraged uses."""
    if source_dict.get("discouraged_uses"):
        return _flatten_to_string(source_dict["discouraged_uses"])
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


def _extract_usage_info(source_dict: Dict[str, Any]) -> Optional[str]:
    """Extract usage information from intended uses or existing uses."""
    items = []
    # Check for usage_notes in existing_uses or other use-related fields
    if source_dict.get("existing_uses"):
        uses = source_dict["existing_uses"]
        if isinstance(uses, list):
            for use in uses:
                if isinstance(use, dict) and use.get("usage_notes"):
                    items.append(str(use.get("usage_notes")))
    if source_dict.get("purposes"):
        purposes = source_dict["purposes"]
        if isinstance(purposes, list):
            for purpose in purposes:
                if isinstance(purpose, dict) and purpose.get("usage_notes"):
                    items.append(str(purpose.get("usage_notes")))
    return " | ".join(items) if items else None


def _extract_machine_annotation_tools(source_dict: Dict[str, Any]) -> Optional[List[str]]:
    """Extract machine annotation tools information."""
    items = []
    if source_dict.get("machine_annotation_tools"):
        tools_data = source_dict["machine_annotation_tools"]
        if isinstance(tools_data, list):
            for tool_obj in tools_data:
                if isinstance(tool_obj, dict):
                    # Extract tool names
                    if tool_obj.get("tools"):
                        tools = tool_obj.get("tools")
                        if isinstance(tools, list):
                            items.extend([str(t) for t in tools if t])
                        elif tools:
                            items.append(str(tools))
        elif isinstance(tools_data, dict):
            if tools_data.get("tools"):
                tools = tools_data.get("tools")
                if isinstance(tools, list):
                    items.extend([str(t) for t in tools if t])
                elif tools:
                    items.append(str(tools))
    return items if items else None


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
    "rai:dataLimitations": {"builder_func": _combine_limitations},
    "rai:dataCollection": {"builder_func": _combine_collection_info},
    "rai:dataCollectionType": {"builder_func": _combine_collection_mechanisms},
    "rai:dataCollectionMissingData": {"builder_func": _extract_missing_data},
    "rai:dataCollectionRawData": {"source_key": "raw_sources", "parser": _flatten_to_string},
    "rai:dataCollectionTimeframe": {"builder_func": _extract_collection_timeframe},
    "rai:dataPreprocessingProtocol": {"source_key": "preprocessing_strategies", "parser": _flatten_to_list},

    # RAI - Data Labeling
    "rai:dataAnnotationProtocol": {"source_key": "labeling_strategies", "parser": _flatten_to_string},
    "rai:dataAnnotationPlatform": {"source_key": None},  # GAP - no D4D mapping
    "rai:dataAnnotationAnalysis": {"builder_func": _extract_annotation_analysis},
    "rai:annotationsPerItem": {"builder_func": _extract_annotations_per_item},
    "rai:machineAnnotationTools": {"builder_func": _extract_machine_annotation_tools},

    # RAI - Safety & Fairness
    "rai:dataBiases": {"builder_func": _combine_biases},
    "rai:dataSocialImpact": {"builder_func": _combine_social_impact},
    "rai:personalSensitiveInformation": {"builder_func": _combine_sensitive_info},
    "rai:dataUseCases": {"builder_func": _combine_use_cases},

    # RAI - Compliance & Governance
    "rai:dataManipulationProtocol": {"source_key": "cleaning_strategies", "parser": _flatten_to_string},
    "rai:dataImputationProtocol": {"builder_func": _extract_imputation_protocol},
    "rai:dataReleaseMaintenancePlan": {"builder_func": _combine_maintenance},

    # Additional metadata
    "funder": {"source_key": "funders", "parser": _flatten_to_string},
    "ethicalReview": {"source_key": "ethical_reviews", "parser": _flatten_to_string},
    "citation": {"source_key": "citation"},
    "principalInvestigator": {"builder_func": _extract_principal_investigator},
    "contactEmail": {"builder_func": _extract_contact_email},
    "usageInfo": {"builder_func": _extract_usage_info},
    "confidentialityLevel": {"builder_func": _extract_confidentiality_level},
    "humanSubject": {"builder_func": _extract_human_subject},
    "governanceCommittee": {"builder_func": _extract_governance_committee},
    "prohibitedUses": {"builder_func": _extract_prohibited_uses},
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

    # RAI (Responsible AI) properties - Data Lifecycle
    "rai:dataLimitations": {"builder_func": _combine_limitations},
    "rai:dataCollection": {"builder_func": _combine_collection_info},
    "rai:dataCollectionType": {"builder_func": _combine_collection_mechanisms},
    "rai:dataCollectionMissingData": {"builder_func": _extract_missing_data},
    "rai:dataCollectionRawData": {"source_key": "raw_sources", "parser": _flatten_to_string},
    "rai:dataCollectionTimeframe": {"builder_func": _extract_collection_timeframe},
    "rai:dataPreprocessingProtocol": {"source_key": "preprocessing_strategies", "parser": _flatten_to_list},

    # RAI - Data Labeling
    "rai:dataAnnotationProtocol": {"source_key": "labeling_strategies", "parser": _flatten_to_string},
    "rai:dataAnnotationPlatform": {"source_key": None},  # GAP - no D4D mapping
    "rai:dataAnnotationAnalysis": {"builder_func": _extract_annotation_analysis},
    "rai:annotationsPerItem": {"builder_func": _extract_annotations_per_item},
    "rai:machineAnnotationTools": {"builder_func": _extract_machine_annotation_tools},

    # RAI - Safety & Fairness
    "rai:dataBiases": {"builder_func": _combine_biases},
    "rai:dataSocialImpact": {"builder_func": _combine_social_impact},
    "rai:personalSensitiveInformation": {"builder_func": _combine_sensitive_info},
    "rai:dataUseCases": {"builder_func": _combine_use_cases},

    # RAI - Compliance & Governance
    "rai:dataManipulationProtocol": {"source_key": "cleaning_strategies", "parser": _flatten_to_string},
    "rai:dataImputationProtocol": {"builder_func": _extract_imputation_protocol},
    "rai:dataReleaseMaintenancePlan": {"builder_func": _combine_maintenance},

    # Additional metadata
    "funder": {"source_key": "funders", "parser": _flatten_to_string},
    "ethicalReview": {"source_key": "ethical_reviews", "parser": _flatten_to_string},
    "citation": {"source_key": "citation"},
    "principalInvestigator": {"builder_func": _extract_principal_investigator},
    "contactEmail": {"builder_func": _extract_contact_email},
    "usageInfo": {"builder_func": _extract_usage_info},
    "confidentialityLevel": {"builder_func": _extract_confidentiality_level},
    "humanSubject": {"builder_func": _extract_human_subject},
    "governanceCommittee": {"builder_func": _extract_governance_committee},
    "prohibitedUses": {"builder_func": _extract_prohibited_uses},
}
