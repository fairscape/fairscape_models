import pytest
from pydantic import ValidationError
from fairscape_models.annotation import Annotation
from fairscape_models.fairscape_base import IdentifierValue

def test_annotation_instantiation(annotation_minimal_data):
    """Test successful instantiation of an Annotation model."""
    annotation = Annotation.model_validate(annotation_minimal_data)
    assert annotation.guid == annotation_minimal_data["@id"]
    assert annotation.description == annotation_minimal_data["description"]

    # Test PROV field auto-population
    assert annotation.used == []  # No usedDataset provided
    assert len(annotation.wasAssociatedWith) == 1
    assert annotation.wasAssociatedWith[0] == annotation_minimal_data["createdBy"]

def test_annotation_short_description(annotation_minimal_data):
    """Test that a short description raises a ValidationError."""
    annotation_minimal_data["description"] = "too short"
    with pytest.raises(ValidationError):
        Annotation.model_validate(annotation_minimal_data)

def test_annotation_with_datasets(annotation_minimal_data):
    """Test PROV field population with usedDataset."""
    annotation_minimal_data["usedDataset"] = [
        {"@id": "ark:59852/dataset-1"},
        {"@id": "ark:59852/dataset-2"}
    ]

    annotation = Annotation.model_validate(annotation_minimal_data)

    # Test PROV:used is populated from usedDataset
    assert len(annotation.used) == 2
    assert all(isinstance(item, IdentifierValue) for item in annotation.used)
    used_ids = [item.guid for item in annotation.used]
    assert "ark:59852/dataset-1" in used_ids
    assert "ark:59852/dataset-2" in used_ids
