import pytest
from pydantic import ValidationError
from fairscape_models.annotation import Annotation

def test_annotation_instantiation(annotation_minimal_data):
    """Test successful instantiation of an Annotation model."""
    annotation = Annotation.model_validate(annotation_minimal_data)
    assert annotation.guid == annotation_minimal_data["@id"]
    assert annotation.description == annotation_minimal_data["description"]

def test_annotation_short_description(annotation_minimal_data):
    """Test that a short description raises a ValidationError."""
    annotation_minimal_data["description"] = "too short"
    with pytest.raises(ValidationError):
        Annotation.model_validate(annotation_minimal_data)
