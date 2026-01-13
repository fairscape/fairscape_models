import pytest
from pydantic import ValidationError
from fairscape_models.model_card import ModelCard
from fairscape_models.fairscape_base import IdentifierValue

@pytest.fixture
def model_card_minimal_data():
    """Minimal data for a valid ModelCard."""
    return {
        "@id": "ark:59852/test-model-card",
        "name": "Test Model Card",
        "author": "Test Model Card Author",
        "description": "This is a test model card with sufficient description.",
        "keywords": ["machine learning", "test"],
        "version": "1.0.0"
    }

def test_model_card_instantiation(model_card_minimal_data):
    """Test successful instantiation of a ModelCard model."""
    model_card = ModelCard.model_validate(model_card_minimal_data)
    assert model_card.guid == model_card_minimal_data["@id"]
    assert model_card.name == model_card_minimal_data["name"]

    # Test PROV field auto-population
    assert len(model_card.wasAttributedTo) == 1
    assert isinstance(model_card.wasAttributedTo[0], str)
    assert model_card.wasAttributedTo[0] == model_card_minimal_data["author"]

def test_model_card_missing_required_field(model_card_minimal_data):
    """Test ValidationError for missing a required field."""
    del model_card_minimal_data["author"]
    with pytest.raises(ValidationError):
        ModelCard.model_validate(model_card_minimal_data)

def test_model_card_with_multiple_authors(model_card_minimal_data):
    """Test PROV field population with multiple authors."""
    model_card_minimal_data["author"] = ["Card Author 1", "Card Author 2"]

    model_card = ModelCard.model_validate(model_card_minimal_data)

    # Test PROV:wasAttributedTo handles list of authors
    assert len(model_card.wasAttributedTo) == 2
    assert all(isinstance(item, str) for item in model_card.wasAttributedTo)
    author_ids = [item for item in model_card.wasAttributedTo]
    assert "Card Author 1" in author_ids
    assert "Card Author 2" in author_ids

def test_model_card_with_generated_by_single(model_card_minimal_data):
    """Test PROV field population with single generatedBy."""
    model_card_minimal_data["generatedBy"] = {"@id": "ark:59852/computation-1"}

    model_card = ModelCard.model_validate(model_card_minimal_data)

    # Test PROV:wasGeneratedBy with single value
    assert len(model_card.wasGeneratedBy) == 1
    assert isinstance(model_card.wasGeneratedBy[0], IdentifierValue)
    assert model_card.wasGeneratedBy[0].guid == "ark:59852/computation-1"


def test_model_card_with_training_dataset_as_string(model_card_minimal_data):
    """Test PROV field population with trainingDataset as string."""
    model_card_minimal_data["trainingDataset"] = "ark:59852/training-data"

    model_card = ModelCard.model_validate(model_card_minimal_data)

    # Test trainingDataset maps to derivedFrom and wasDerivedFrom
    assert len(model_card.derivedFrom) == 1
    assert model_card.derivedFrom[0] == "ark:59852/training-data"
    assert len(model_card.wasDerivedFrom) == 1

def test_model_card_with_training_dataset_as_list(model_card_minimal_data):
    """Test PROV field population with trainingDataset as list."""
    model_card_minimal_data["trainingDataset"] = [
        {"@id": "ark:59852/training-data-1"},
        {"@id": "ark:59852/training-data-2"}
    ]

    model_card = ModelCard.model_validate(model_card_minimal_data)

    # Test trainingDataset maps to derivedFrom and wasDerivedFrom
    assert len(model_card.derivedFrom) == 2
    assert all(isinstance(item, IdentifierValue) for item in model_card.derivedFrom)
    assert len(model_card.wasDerivedFrom) == 2

def test_model_card_with_derived_from(model_card_minimal_data):
    """Test PROV field population with derivedFrom."""
    model_card_minimal_data["derivedFrom"] = [
        {"@id": "ark:59852/model-source"}
    ]

    model_card = ModelCard.model_validate(model_card_minimal_data)

    # Test PROV:wasDerivedFrom
    assert len(model_card.wasDerivedFrom) == 1
    assert isinstance(model_card.wasDerivedFrom[0], IdentifierValue)
    assert model_card.wasDerivedFrom[0].guid == "ark:59852/model-source"

def test_model_card_derived_from_takes_precedence(model_card_minimal_data):
    """Test that derivedFrom takes precedence over trainingDataset."""
    model_card_minimal_data["trainingDataset"] = [{"@id": "ark:59852/training-data"}]
    model_card_minimal_data["derivedFrom"] = [{"@id": "ark:59852/model-source"}]

    model_card = ModelCard.model_validate(model_card_minimal_data)

    # derivedFrom should remain as specified, not be overwritten by trainingDataset
    assert len(model_card.derivedFrom) == 1
    assert model_card.derivedFrom[0].guid == "ark:59852/model-source"

def test_model_card_edge_case_empty_author():
    """Test PROV field population when author is falsy (defensive code path)."""
    # Test with empty list for author (valid but falsy)
    model_card_data = {
        "@id": "ark:59852/test-model-card",
        "name": "Test Model Card",
        "author": [],
        "description": "This is a test model card with sufficient description.",
        "keywords": ["test"],
        "version": "1.0.0"
    }

    model_card = ModelCard.model_validate(model_card_data)

    # Should hit the else clause and set wasAttributedTo to empty list
    assert model_card.wasAttributedTo == []

def test_model_card_edge_case_no_generated_by():
    """Test PROV field population when generatedBy is None."""
    model_card_data = {
        "@id": "ark:59852/test-model-card",
        "name": "Test Model Card",
        "author": "Test Author",
        "description": "This is a test model card with sufficient description.",
        "keywords": ["test"],
        "version": "1.0.0",
        "generatedBy": None
    }

    model_card = ModelCard.model_validate(model_card_data)

    # Should set wasGeneratedBy to empty list
    assert model_card.wasGeneratedBy == []
