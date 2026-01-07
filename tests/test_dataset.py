import pytest
from pydantic import ValidationError
from fairscape_models.dataset import Dataset
from fairscape_models.fairscape_base import IdentifierValue

def test_dataset_instantiation(dataset_minimal_data):
    """Test successful instantiation of a Dataset model."""
    dataset = Dataset.model_validate(dataset_minimal_data)
    assert dataset.guid == dataset_minimal_data["@id"]
    assert dataset.name == dataset_minimal_data["name"]
    assert dataset.fileFormat == dataset_minimal_data["format"]

    # Test PROV field auto-population
    assert dataset.wasGeneratedBy == []  # No generatedBy provided
    assert dataset.wasDerivedFrom == []  # No derivedFrom provided
    assert len(dataset.wasAttributedTo) == 1
    assert isinstance(dataset.wasAttributedTo[0], IdentifierValue)
    assert dataset.wasAttributedTo[0].guid == dataset_minimal_data["author"]

def test_dataset_missing_required_field(dataset_minimal_data):
    """Test that a ValidationError is raised for a missing required field."""
    del dataset_minimal_data["name"]
    with pytest.raises(ValidationError):
        Dataset.model_validate(dataset_minimal_data)

def test_dataset_alias_serialization(dataset_minimal_data):
    """Test that aliases are correctly handled during serialization."""
    dataset = Dataset.model_validate(dataset_minimal_data)
    serialized_data = dataset.model_dump(by_alias=True)
    assert "@id" in serialized_data
    assert "guid" not in serialized_data
    assert "format" in serialized_data
    assert "fileFormat" not in serialized_data

def test_dataset_custom_validator(dataset_minimal_data):
    """Test the validation alias for dataSchema."""
    # Test that None is accepted
    dataset_minimal_data_v1 = {**dataset_minimal_data, "schema": None}
    dataset1 = Dataset.model_validate(dataset_minimal_data_v1)
    assert dataset1.dataSchema is None

    # Test that a valid IdentifierValue is accepted using the 'schema' alias
    schema_id = {"@id": "ark:59852/test-schema"}
    # Use the 'schema' alias, which is what the model expects for validation
    dataset_minimal_data_v3 = {**dataset_minimal_data, "schema": schema_id}
    dataset3 = Dataset.model_validate(dataset_minimal_data_v3)

    # Assert that the dataSchema attribute is correctly populated
    assert dataset3.dataSchema is not None
    assert dataset3.dataSchema.guid == schema_id["@id"]

def test_dataset_with_provenance(dataset_minimal_data):
    """Test PROV field population with generatedBy and derivedFrom."""
    dataset_minimal_data["generatedBy"] = [{"@id": "ark:59852/computation-1"}]
    dataset_minimal_data["derivedFrom"] = [{"@id": "ark:59852/dataset-source"}]
    dataset_minimal_data["author"] = ["Author 1", "Author 2"]  # Test list of authors

    dataset = Dataset.model_validate(dataset_minimal_data)

    # Test PROV fields
    assert len(dataset.wasGeneratedBy) == 1
    assert isinstance(dataset.wasGeneratedBy[0], IdentifierValue)
    assert dataset.wasGeneratedBy[0].guid == "ark:59852/computation-1"

    assert len(dataset.wasDerivedFrom) == 1
    assert isinstance(dataset.wasDerivedFrom[0], IdentifierValue)
    assert dataset.wasDerivedFrom[0].guid == "ark:59852/dataset-source"

    assert len(dataset.wasAttributedTo) == 2
    assert all(isinstance(item, IdentifierValue) for item in dataset.wasAttributedTo)
    author_ids = [item.guid for item in dataset.wasAttributedTo]
    assert "Author 1" in author_ids
    assert "Author 2" in author_ids

def test_dataset_edge_case_empty_author():
    """Test PROV field population when author is falsy (defensive code path)."""
    # Test with empty list for author (valid but falsy)
    dataset_data = {
        "@id": "ark:59852/test-dataset",
        "name": "Test Dataset",
        "author": [],
        "datePublished": "2023-11-09",
        "description": "This is a test dataset with sufficient description.",
        "keywords": ["test", "dataset"],
        "format": "text/csv"
    }

    dataset = Dataset.model_validate(dataset_data)

    # Should hit the else clause and set wasAttributedTo to empty list
    assert dataset.wasAttributedTo == []