import pytest
from pathlib import Path
from pydantic import ValidationError
from fairscape_models.dataset import (
    Dataset,
    Split,
    SplitType,
    _count_csv,
    _human_size,
)
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


def test_count_csv_with_data(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("a,b,c\n1,2,3\n4,5,6\n")
    rows, cols = _count_csv(p, ",")
    assert rows == 2
    assert cols == 3


def test_count_csv_empty_file(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("")
    rows, cols = _count_csv(p, ",")
    assert rows == 0
    assert cols == 0


def test_count_csv_tsv(tmp_path):
    p = tmp_path / "data.tsv"
    p.write_text("a\tb\n1\t2\n")
    rows, cols = _count_csv(p, "\t")
    assert rows == 1
    assert cols == 2


def test_human_size_bytes():
    assert _human_size(500) == "500 B"


def test_human_size_kb():
    assert _human_size(2048) == "2.0 KB"


def test_human_size_mb():
    assert _human_size(5 * 1024 * 1024) == "5.0 MB"


def test_human_size_terabytes_clamps():
    # Forces the `unit == "TB"` early-return branch
    big = 5 * 1024 ** 4
    assert _human_size(big).endswith("TB")


def test_split_model_defaults():
    split = Split(name="train")
    assert split.name == "train"
    assert split.splitType is None
    assert split.isSample is None


def test_split_model_with_fields():
    split = Split(
        name="train",
        description="training split",
        splitType=SplitType.TRAIN,
        query="SELECT *",
        queryType="sql",
        sourceDatasets=[IdentifierValue(**{"@id": "ark:59852/src"})],
        isSample=True,
        isRandom=False,
        samplingStrategy="stratified",
    )
    assert split.splitType == SplitType.TRAIN
    assert split.sourceDatasets[0].guid == "ark:59852/src"


def _make_dataset(tmp_path, content_url=None, file_format="text/csv"):
    return Dataset.model_validate({
        "@id": "ark:59852/tabular",
        "name": "Tabular",
        "author": "A",
        "datePublished": "2024-01-01",
        "description": "A tabular dataset for testing summary stats.",
        "keywords": ["t"],
        "format": file_format,
        "contentUrl": content_url,
    })


def test_add_summary_stats_with_explicit_file_path(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b\n1,2\n3,4\n5,6\n")
    ds = _make_dataset(tmp_path)
    stats = ds.add_summary_stats(file_path=csv_path)
    assert ds.rowCount == 3
    assert ds.columnCount == 2
    assert ds.sampleSize == 3
    assert ds.contentSize.endswith("B")
    assert isinstance(ds.hasSummaryStatistics, IdentifierValue)
    assert stats.guid == f"{ds.guid}/summary-stats"
    assert stats.rowCount == 3
    assert stats.fileFormat == "application/json"
    assert "summary-statistics" in stats.keywords


def test_add_summary_stats_preserves_sample_size(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b\n1,2\n")
    ds = _make_dataset(tmp_path)
    ds.sampleSize = 42
    ds.add_summary_stats(file_path=csv_path)
    assert ds.sampleSize == 42


def test_add_summary_stats_tsv_via_file_format(tmp_path):
    # Use .tsv extension so _require_tabular passes, and a tab-formatted file
    tsv_path = tmp_path / "data.tsv"
    tsv_path.write_text("a\tb\n1\t2\n")
    ds = _make_dataset(tmp_path, file_format="tab-separated-values")
    ds.add_summary_stats(file_path=tsv_path)
    assert ds.columnCount == 2
    assert ds.rowCount == 1


def test_add_summary_stats_file_path_missing(tmp_path):
    ds = _make_dataset(tmp_path)
    with pytest.raises(FileNotFoundError):
        ds.add_summary_stats(file_path=tmp_path / "nope.csv")


def test_add_summary_stats_no_content_url(tmp_path):
    ds = _make_dataset(tmp_path)
    with pytest.raises(ValueError, match="no contentUrl"):
        ds.add_summary_stats()


def test_add_summary_stats_remote_url_not_supported(tmp_path):
    ds = _make_dataset(tmp_path, content_url="https://example.org/data.csv")
    with pytest.raises(NotImplementedError):
        ds.add_summary_stats()


def test_add_summary_stats_file_url_without_crate_root(tmp_path):
    ds = _make_dataset(tmp_path, content_url="file:///data.csv")
    with pytest.raises(ValueError, match="crate-relative"):
        ds.add_summary_stats()


def test_add_summary_stats_file_url_with_crate_root(tmp_path):
    csv_path = tmp_path / "inner.csv"
    csv_path.write_text("a,b\n1,2\n")
    ds = _make_dataset(tmp_path, content_url="file:///inner.csv")
    ds.add_summary_stats(crate_root=tmp_path)
    assert ds.rowCount == 1
    assert ds.columnCount == 2


def test_add_summary_stats_content_url_list(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a\n1\n")
    ds = _make_dataset(tmp_path, content_url=[str(csv_path)])
    ds.add_summary_stats()
    assert ds.rowCount == 1


def test_add_summary_stats_relative_content_url_with_crate_root(tmp_path):
    csv_path = tmp_path / "rel.csv"
    csv_path.write_text("a,b\n1,2\n")
    ds = _make_dataset(tmp_path, content_url="rel.csv")
    ds.add_summary_stats(crate_root=tmp_path)
    assert ds.rowCount == 1


def test_add_summary_stats_resolved_path_missing(tmp_path):
    ds = _make_dataset(tmp_path, content_url=str(tmp_path / "missing.csv"))
    with pytest.raises(FileNotFoundError, match="Resolved contentUrl"):
        ds.add_summary_stats()


def test_add_summary_stats_non_tabular_format(tmp_path):
    bad_path = tmp_path / "data.parquet"
    bad_path.write_bytes(b"not tabular")
    ds = _make_dataset(tmp_path, file_format="application/parquet")
    with pytest.raises(ValueError, match="not csv/tsv"):
        ds.add_summary_stats(file_path=bad_path)