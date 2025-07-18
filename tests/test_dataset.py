import pytest
from pydantic import ValidationError
from fairscape_models.dataset import Dataset

def test_dataset_instantiation(dataset_minimal_data):
    """Test successful instantiation of a Dataset model."""
    dataset = Dataset.model_validate(dataset_minimal_data)
    assert dataset.guid == dataset_minimal_data["@id"]
    assert dataset.name == dataset_minimal_data["name"]
    assert dataset.fileFormat == dataset_minimal_data["format"]

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