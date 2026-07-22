"""
End-to-end infer/validate tests per schema type. All fixtures are generated or
hand-written in tmp_path — no binary fixtures are read from disk. Each test group
is skipped if its optional dependency is missing.
"""

import numpy as np
import pytest

from fairscape_models.schema import (
    HDF5Schema,
    ImageSchema,
    SignalSchema,
    TabularSchema,
    infer_schema,
    validate_schema,
)
from fairscape_models.schema.ontology import anatomy_terms, unit_terms


# --------------------------------------------------------------------------- #
# ontology (stdlib only, always runs)
# --------------------------------------------------------------------------- #

def test_unit_terms_known_and_unknown():
    ucum, qudt = unit_terms("mV")
    assert ucum == "mV"
    assert qudt == "http://qudt.org/vocab/unit/MilliV"
    assert unit_terms("notaunit") == ("notaunit", None)
    assert unit_terms(None) == (None, None)


def test_anatomy_terms_crosswalk():
    label, url = anatomy_terms("CHEST")
    assert url and url.startswith("http://snomed.info/id/")
    assert anatomy_terms("madeuppart") == ("madeuppart", None)


# --------------------------------------------------------------------------- #
# tabular (frictionless)
# --------------------------------------------------------------------------- #

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


# --------------------------------------------------------------------------- #
# hdf5 (h5py)
# --------------------------------------------------------------------------- #

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


# --------------------------------------------------------------------------- #
# signal (wfdb)
# --------------------------------------------------------------------------- #

wfdb = pytest.importorskip("wfdb")


@pytest.fixture
def wfdb_record(tmp_path):
    rec = "sig"
    header = (
        f"{rec} 2 250 100\n"
        f"{rec}.dat 16 200(0)/mV 16 0 0 0 0 MLII\n"
        f"{rec}.dat 16 200(0)/mV 16 0 0 0 0 V5\n"
    )
    (tmp_path / f"{rec}.hea").write_text(header)
    np.zeros((100, 2), dtype="<i2").tofile(tmp_path / f"{rec}.dat")
    return str(tmp_path / f"{rec}.hea")


def test_signal_infer(wfdb_record):
    schema = SignalSchema.infer(wfdb_record, name="sig", description="d")
    assert schema.samplingFrequency == 250
    assert schema.numberOfSamples == 100
    assert schema.samplingFrequencyUnitURL == "http://qudt.org/vocab/unit/HZ"
    ch = schema.properties["MLII"]
    assert ch.unit == "mV"
    assert ch.unitURL == "http://qudt.org/vocab/unit/MilliV"
    assert ch.gain == 200


def test_signal_validate_clean_and_drift(wfdb_record):
    schema = SignalSchema.infer(wfdb_record, name="sig", description="d")
    assert validate_schema(schema, wfdb_record) == []
    schema.properties["MLII"].gain = 999.0
    errors = validate_schema(schema, wfdb_record)
    assert any(e.failed_keyword == "const" and e.field == "MLII.gain" for e in errors)


# --------------------------------------------------------------------------- #
# image (pydicom)
# --------------------------------------------------------------------------- #

pydicom = pytest.importorskip("pydicom")


@pytest.fixture
def dicom_file(tmp_path):
    from pydicom.dataset import Dataset, FileDataset
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid

    fm = Dataset()
    fm.MediaStorageSOPClassUID = generate_uid()
    fm.MediaStorageSOPInstanceUID = generate_uid()
    fm.TransferSyntaxUID = ExplicitVRLittleEndian
    p = tmp_path / "t.dcm"
    ds = FileDataset(str(p), {}, file_meta=fm, preamble=b"\0" * 128)
    ds.Modality = "CT"
    ds.Rows = 64
    ds.Columns = 48
    ds.PixelSpacing = [0.5, 0.6]
    ds.BitsAllocated = 16
    ds.PixelRepresentation = 1
    ds.BodyPartExamined = "CHEST"
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.save_as(str(p))
    return str(p)


def test_image_infer(dicom_file):
    schema = ImageSchema.infer(dicom_file, name="img", description="d")
    assert schema.dicomModalityCode == "CT"
    assert schema.modalityURL == "http://snomed.info/id/77477000"
    assert schema.dtype == "int16"
    assert schema.properties["x"].size == 48
    assert schema.properties["y"].size == 64
    assert schema.properties["x"].unit == "mm"
    assert schema.anatomyURL and schema.anatomyURL.startswith("http://snomed.info/id/")


def test_image_validate_clean_and_drift(dicom_file):
    schema = ImageSchema.infer(dicom_file, name="img", description="d")
    assert validate_schema(schema, dicom_file) == []
    schema.properties["x"].size = 999
    errors = validate_schema(schema, dicom_file)
    assert any(e.failed_keyword == "const" and e.field == "x.size" for e in errors)


def test_infer_schema_dispatches_by_extension(dicom_file):
    assert isinstance(infer_schema(dicom_file, name="a", description="d"), ImageSchema)
