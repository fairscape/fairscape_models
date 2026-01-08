import pytest
from pydantic import ValidationError
from fairscape_models.mlmodel import MLModel
from fairscape_models.fairscape_base import IdentifierValue

@pytest.fixture
def mlmodel_minimal_data():
    """Minimal data for a valid MLModel."""
    return {
        "@id": "ark:59852/test-mlmodel",
        "name": "Test ML Model",
        "author": "Test ML Author",
        "description": "This is a test ML model with sufficient description.",
        "format": "application/x-pickle"
    }

def test_mlmodel_instantiation(mlmodel_minimal_data):
    """Test successful instantiation of an MLModel model."""
    mlmodel = MLModel.model_validate(mlmodel_minimal_data)
    assert mlmodel.guid == mlmodel_minimal_data["@id"]
    assert mlmodel.name == mlmodel_minimal_data["name"]

    # Test PROV field auto-population
    assert len(mlmodel.wasAttributedTo) == 1
    assert isinstance(mlmodel.wasAttributedTo[0], str)
    assert mlmodel.wasAttributedTo[0] == mlmodel_minimal_data["author"]

def test_mlmodel_missing_required_field(mlmodel_minimal_data):
    """Test ValidationError for missing a required field."""
    del mlmodel_minimal_data["author"]
    with pytest.raises(ValidationError):
        MLModel.model_validate(mlmodel_minimal_data)

def test_mlmodel_short_description(mlmodel_minimal_data):
    """Test that a short description raises a ValidationError."""
    mlmodel_minimal_data["description"] = "too short"
    with pytest.raises(ValidationError):
        MLModel.model_validate(mlmodel_minimal_data)

def test_mlmodel_with_multiple_authors(mlmodel_minimal_data):
    """Test PROV field population with multiple authors."""
    mlmodel_minimal_data["author"] = ["ML Author 1", "ML Author 2"]

    mlmodel = MLModel.model_validate(mlmodel_minimal_data)

    # Test PROV:wasAttributedTo handles list of authors
    assert len(mlmodel.wasAttributedTo) == 2
    assert all(isinstance(item, str) for item in mlmodel.wasAttributedTo)
    author_ids = [item for item in mlmodel.wasAttributedTo]
    assert "ML Author 1" in author_ids
    assert "ML Author 2" in author_ids

def test_mlmodel_with_generated_by_single(mlmodel_minimal_data):
    """Test PROV field population with single generatedBy."""
    mlmodel_minimal_data["generatedBy"] = {"@id": "ark:59852/computation-1"}

    mlmodel = MLModel.model_validate(mlmodel_minimal_data)

    # Test PROV:wasGeneratedBy with single value
    assert len(mlmodel.wasGeneratedBy) == 1
    assert isinstance(mlmodel.wasGeneratedBy[0], IdentifierValue)
    assert mlmodel.wasGeneratedBy[0].guid == "ark:59852/computation-1"

def test_mlmodel_with_generated_by_list(mlmodel_minimal_data):
    """Test PROV field population with list of generatedBy."""
    mlmodel_minimal_data["generatedBy"] = [
        {"@id": "ark:59852/computation-1"},
        {"@id": "ark:59852/computation-2"}
    ]

    mlmodel = MLModel.model_validate(mlmodel_minimal_data)

    # Test PROV:wasGeneratedBy with list
    assert len(mlmodel.wasGeneratedBy) == 2
    assert all(isinstance(item, IdentifierValue) for item in mlmodel.wasGeneratedBy)
    generated_ids = [item.guid for item in mlmodel.wasGeneratedBy]
    assert "ark:59852/computation-1" in generated_ids
    assert "ark:59852/computation-2" in generated_ids

def test_mlmodel_with_derived_from(mlmodel_minimal_data):
    """Test PROV field population with derivedFrom."""
    mlmodel_minimal_data["derivedFrom"] = [
        {"@id": "ark:59852/model-source"}
    ]

    mlmodel = MLModel.model_validate(mlmodel_minimal_data)

    # Test PROV:wasDerivedFrom
    assert len(mlmodel.wasDerivedFrom) == 1
    assert isinstance(mlmodel.wasDerivedFrom[0], IdentifierValue)
    assert mlmodel.wasDerivedFrom[0].guid == "ark:59852/model-source"

def test_mlmodel_edge_case_empty_author():
    """Test PROV field population when author is falsy (defensive code path)."""
    # Test with empty list for author (valid but falsy)
    mlmodel_data = {
        "@id": "ark:59852/test-mlmodel",
        "name": "Test Model",
        "author": [],
        "description": "This is a test ML model with sufficient description.",
        "format": "application/x-pickle"
    }

    mlmodel = MLModel.model_validate(mlmodel_data)

    # Should hit the else clause and set wasAttributedTo to empty list
    assert mlmodel.wasAttributedTo == []
