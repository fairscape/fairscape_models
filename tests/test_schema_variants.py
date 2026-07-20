"""Dispatch + parsing tests for the typed schema hierarchy (no data files)."""

import pytest

from fairscape_models.schema import (
    HDF5Schema,
    ImageSchema,
    NDArraySchema,
    Schema,
    SignalSchema,
    TabularSchema,
    parse_schema,
)


def _base_doc(**extra):
    doc = {
        "@id": "ark:59853/schema-x",
        "@type": "evi:Schema",
        "name": "x",
        "description": "d",
        "properties": {"col": {"description": "c", "index": 0, "type": "integer"}},
    }
    doc.update(extra)
    return doc


@pytest.mark.parametrize("tag,cls", [
    ("tabular", TabularSchema),
    ("signal", SignalSchema),
    ("image", ImageSchema),
    ("ndarray", NDArraySchema),
    ("hdf5", HDF5Schema),
])
def test_parse_dispatch_by_tag(tag, cls):
    doc = _base_doc()
    doc["EVI:schemaType"] = tag
    assert isinstance(parse_schema(doc), cls)


def test_untagged_document_is_tabular():
    assert isinstance(parse_schema(_base_doc()), TabularSchema)


def test_unknown_tag_falls_back_to_base_schema():
    doc = _base_doc()
    doc["EVI:schemaType"] = "somethingElse"
    result = parse_schema(doc)
    assert isinstance(result, Schema)
    assert not isinstance(result, TabularSchema)


def test_legacy_hdf5_document_normalizes_to_hdf5schema():
    legacy = {
        "@id": "ark:59853/schema-legacy",
        "@type": "evi:Schema",
        "name": "legacy",
        "description": "d",
        "properties": {
            "/grp/ds": {
                "description": "legacy dataset",
                "hdf5-path": "/grp/ds",
                "properties": {
                    "colA": {"type": "year"},           # legacy non-canonical type
                    "colB": {"type": "string", "index": 1},
                },
            }
        },
    }
    result = parse_schema(legacy)
    assert isinstance(result, HDF5Schema)
    ds = result.properties["/grp/ds"]
    assert ds.type == "object"
    # legacy 'year' canonicalizes to integer, original kept under source-type
    assert ds.properties["colA"].type == "integer"
    assert ds.properties["colA"].model_extra.get("source-type") == "year"


def test_non_tabular_dump_drops_tabular_fields():
    # No @type provided -> NonTabularSchema default (EVI:Schema) applies.
    doc = {
        "@id": "ark:59853/schema-x",
        "name": "x",
        "description": "d",
        "EVI:schemaType": "signal",
        "properties": {"MLII": {"description": "ch", "index": 0, "type": "number"}},
    }
    dumped = parse_schema(doc).model_dump(by_alias=True, exclude_none=True)
    assert dumped["EVI:schemaType"] == "signal"
    assert dumped["@type"] == "EVI:Schema"
    # tabular-only fields are neutralized to None and drop out
    for key in ("separator", "header", "type", "additionalProperties"):
        assert key not in dumped
