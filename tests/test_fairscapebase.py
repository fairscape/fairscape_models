import pytest
from pydantic import ValidationError
from fairscape_models.fairscape_base import (
    Identifier,
    IdentifierValue,
    IdentifierPropertyValue,
    ClassType,
    normalize_class_type
)

def test_identifier_value():
    iv = IdentifierValue.model_validate({"@id": "test-id"})
    assert iv.guid == "test-id"
    assert iv.model_dump(by_alias=True) == {"@id": "test-id"}

def test_identifier_property_value():
    ipv = IdentifierPropertyValue.model_validate({
        "@type": "PropertyValue",
        "name": "test-name",
        "value": "test-value"
    })
    assert ipv.name == "test-name"
    assert ipv.value == "test-value"
    assert ipv.metadataType == "PropertyValue"

def test_identifier_missing_name():
    with pytest.raises(ValidationError):
        Identifier.model_validate({
            "@id": "test-id",
            "@type": "Dataset"
        })

@pytest.mark.parametrize("input_val, expected", [
    ("Dataset", ClassType.DATASET),
    ("Software", ClassType.SOFTWARE),
    ("ROCrate", ClassType.ROCRATE),
    ("https://w3id.org/EVI#Dataset", ClassType.DATASET),
    ("evi:Schema", ClassType.SCHEMA),
    (" computation ", ClassType.COMPUTATION),
    (ClassType.DATASET, ClassType.DATASET)
])
def test_normalize_class_type_valid(input_val, expected):
    """Test normalization of various valid class type strings."""
    assert normalize_class_type(input_val) == expected

def test_normalize_class_type_invalid():
    """Test that an invalid class type string raises a ValueError."""
    with pytest.raises(ValueError, match="Invalid class type: InvalidType"):
        normalize_class_type("InvalidType")