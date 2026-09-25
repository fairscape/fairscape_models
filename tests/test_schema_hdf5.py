"""HDF5 schema infer/validate. Skipped without the schema-hdf5 extra."""

import pytest

from fairscape_models.schema import HDF5Schema, validate_schema

np = pytest.importorskip("numpy")
h5py = pytest.importorskip("h5py")


@pytest.fixture
def h5_file(tmp_path):
    p = tmp_path / "d.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("a", data=np.zeros((3,), dtype="f8"))
        grp = f.create_group("grp")
        grp.create_dataset("b", data=np.zeros((2, 4), dtype="i4"),
                           chunks=(1, 4), compression="gzip")
        comp = np.zeros(2, dtype=[("id", "i8"), ("score", "f4")])
        f.create_dataset("c", data=comp)
    return str(p)


def test_hdf5_infer_structure(h5_file):
    schema = HDF5Schema.infer(h5_file, name="h5", description="d")
    assert schema.properties["a"].shape == [3]
    assert schema.properties["a"].dtype == "float64"
    b = schema.properties["grp/b"]
    assert b.shape == [2, 4]
    assert b.chunks == [1, 4]
    assert b.compression == "gzip"
    c = schema.properties["c"]
    assert c.type == "object"
    assert set(c.properties) == {"id", "score"}


def test_hdf5_validate_clean(h5_file):
    schema = HDF5Schema.infer(h5_file, name="h5", description="d")
    assert validate_schema(schema, h5_file) == []


def test_hdf5_validate_drift(h5_file):
    schema = HDF5Schema.infer(h5_file, name="h5", description="d")
    schema.properties["a"].shape = [9]
    schema.properties["grp/b"].dtype = "int64"
    errors = validate_schema(schema, h5_file)
    keywords = {(e.failed_keyword, e.field) for e in errors}
    assert ("const", "a.shape") in keywords
    assert ("type", "grp/b.dtype") in keywords


def test_hdf5_validate_missing_dataset(h5_file):
    schema = HDF5Schema.infer(h5_file, name="h5", description="d")
    from fairscape_models.schema import DatasetProperty
    schema.properties["ghost"] = DatasetProperty(
        description="x", index=99, type="array", shape=[1])
    errors = validate_schema(schema, h5_file)
    assert any(e.failed_keyword == "required" and e.field == "ghost" for e in errors)
