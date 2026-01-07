import pytest
from pydantic import ValidationError
from fairscape_models.software import Software
from fairscape_models.fairscape_base import IdentifierValue

def test_software_instantiation(software_minimal_data):
    """Test successful instantiation of a Software model."""
    software = Software.model_validate(software_minimal_data)
    assert software.guid == software_minimal_data["@id"]
    assert software.name == software_minimal_data["name"]

    # Test PROV field auto-population
    assert len(software.wasAttributedTo) == 1
    assert software.wasAttributedTo[0] == software_minimal_data["author"]

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

def test_software_with_multiple_authors(software_minimal_data):
    """Test PROV field population with multiple authors."""
    software_minimal_data["author"] = ["Author 1", "Author 2", "Author 3"]

    software = Software.model_validate(software_minimal_data)

    # Test PROV:wasAttributedTo handles list of authors
    assert len(software.wasAttributedTo) == 3
    assert "Author 1" in software.wasAttributedTo
    assert "Author 2" in software.wasAttributedTo
    assert "Author 3" in software.wasAttributedTo

def test_software_edge_case_empty_author():
    """Test PROV field population when author is falsy (defensive code path)."""
    # Test with empty list for author (valid but falsy)
    software_data = {
        "@id": "ark:59852/test-software",
        "name": "Test Software",
        "author": [],
        "dateModified": "2023-11-09",
        "description": "This is a test software with a good description.",
        "format": "application/x-python"
    }

    software = Software.model_validate(software_data)

    # Should hit the else clause and set wasAttributedTo to empty list
    assert software.wasAttributedTo == []