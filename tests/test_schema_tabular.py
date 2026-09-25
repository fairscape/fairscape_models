"""Tabular schema infer/validate. Skipped without the schema-tabular extra."""

import pytest

from fairscape_models.schema import TabularSchema, validate_schema

frictionless = pytest.importorskip("frictionless")


def test_tabular_csv_infer_validate(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("id,score,label\n1,0.5,a\n2,1.5,b\n")
    schema = TabularSchema.infer(str(p), name="csv", description="d")
    assert schema.properties["id"].type == "integer"
    assert schema.properties["score"].type == "number"
    assert schema.properties["label"].type == "string"
    assert schema.separator == ","
    assert validate_schema(schema, str(p)) == []


def test_tabular_tsv_separator(tmp_path):
    p = tmp_path / "t.tsv"
    p.write_text("id\tscore\n1\t0.5\n")
    schema = TabularSchema.infer(str(p), name="tsv", description="d")
    assert schema.separator == "\t"
    assert validate_schema(schema, str(p)) == []


def test_tabular_type_mismatch_reports_error(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("id,label\n1,a\n2,b\n")
    schema = TabularSchema.infer(str(p), name="csv", description="d")
    schema.properties["label"].type = "integer"
    errors = validate_schema(schema, str(p))
    assert errors
    assert any(e.field == "label" for e in errors)


def test_tabular_parquet_infer_validate(tmp_path):
    pytest.importorskip("pyarrow")
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    p = tmp_path / "t.parquet"
    df = pd.DataFrame({
        "id": [1, 2],
        "score": [0.5, 1.5],
        "when": pd.to_datetime(["2024-01-01", "2024-02-01"]),
    })
    pq.write_table(pa.Table.from_pandas(df), str(p))
    schema = TabularSchema.infer(str(p), name="pq", description="d")
    assert schema.properties["id"].type == "integer"
    # datetime column keeps a source-type so validation rebuilds a DatetimeField
    assert schema.properties["when"].model_extra.get("source-type") == "datetime"
    assert schema.separator is None
    assert validate_schema(schema, str(p)) == []


def test_tabular_spanning_array(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("embed_0,embed_1,embed_2\n0.1,0.2,0.3\n0.4,0.5,0.6\n")
    schema = TabularSchema.model_validate({
        "@id": "ark:59853/schema-span",
        "name": "span",
        "description": "d",
        "properties": {
            "embed": {
                "description": "vector", "index": "0::", "type": "array",
                "min-items": 3, "max-items": 3,
                "items": {"type": "number"},
            }
        },
    })
    assert validate_schema(schema, str(p)) == []
