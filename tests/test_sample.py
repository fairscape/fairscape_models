import pytest
from pydantic import ValidationError
from fairscape_models.sample import Sample


@pytest.fixture
def minimal_sample_data():
    return {
        "@id": "ark:59852/test-sample",
        "name": "Test Sample",
        "author": "tester",
        "description": "A test sample",
        "keywords": ["test"],
    }


def test_sample_populate_prov_fields(minimal_sample_data):
    """model_validator sets metadataType to the EVI Sample type list."""
    sample = Sample.model_validate(minimal_sample_data)
    assert "prov:Entity" in sample.metadataType
    assert "https://w3id.org/EVI#Sample" in sample.metadataType


def test_sample_prov_fields_override_custom_type(minimal_sample_data):
    """metadataType is always normalized even if a custom value is supplied."""
    minimal_sample_data["@type"] = "CustomType"
    sample = Sample.model_validate(minimal_sample_data)
    assert sample.metadataType == ["prov:Entity", "https://w3id.org/EVI#Sample"]
