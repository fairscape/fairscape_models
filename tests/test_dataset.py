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
    assert isinstance(dataset.wasAttributedTo[0], str)
    assert dataset.wasAttributedTo[0] == dataset_minimal_data["author"]

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
    assert all(isinstance(item, str) for item in dataset.wasAttributedTo)
    author_ids = [item for item in dataset.wasAttributedTo]
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


def test_dataset_default_fields_present_in_json(dataset_minimal_data):
    """Fields with non-None defaults appear in serialized JSON even when not explicitly provided."""
    from fairscape_models.fairscape_base import DATASET_TYPE
    dataset = Dataset.model_validate(dataset_minimal_data)
    output = dataset.model_dump(by_alias=True, exclude_none=True)

    # version has default "0.1.0"
    assert "version" in output
    assert output["version"] == "0.1.0"

    # fairscapeVersion is always injected from _version
    assert "fairscapeVersion" in output

    # additionalType defaults to DATASET_TYPE
    assert "additionalType" in output
    assert output["additionalType"] == DATASET_TYPE

    # empty-list defaults still serialize
    assert "isPartOf" in output
    assert output["isPartOf"] == []


def test_dataset_null_optional_fields_absent_from_json(dataset_minimal_data):
    """Optional fields left as None are excluded when serializing with exclude_none=True."""
    dataset = Dataset.model_validate(dataset_minimal_data)
    output = dataset.model_dump(by_alias=True, exclude_none=True)

    for null_field in ("associatedPublication", "additionalDocumentation", "contentUrl", "md5", "hash", "sha256"):
        assert null_field not in output, f"expected {null_field!r} to be absent when None"


def test_dataset_custom_type_overwritten_by_validator(dataset_minimal_data):
    """A caller-supplied @type is always replaced by the model validator."""
    dataset_minimal_data["@type"] = "CustomType"
    dataset = Dataset.model_validate(dataset_minimal_data)
    assert dataset.metadataType == ["prov:Entity", "https://w3id.org/EVI#Dataset"]