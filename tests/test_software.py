import pytest
from pydantic import ValidationError
from fairscape_models.software import Software

def test_software_instantiation(software_minimal_data):
    """Test successful instantiation of a Software model."""
    software = Software.model_validate(software_minimal_data)
    assert software.guid == software_minimal_data["@id"]
    assert software.name == software_minimal_data["name"]

def test_software_missing_required_field(software_minimal_data):
    """Test ValidationError for missing a required field."""
    del software_minimal_data["author"]
    with pytest.raises(ValidationError):
        Software.model_validate(software_minimal_data)

def test_software_short_description(software_minimal_data):
    """Test that a short description raises a ValidationError."""
    software_minimal_data["description"] = "too short"
    with pytest.raises(ValidationError):
        Software.model_validate(software_minimal_data)