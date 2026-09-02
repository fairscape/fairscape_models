"""
End-to-end infer/validate tests per schema type. All fixtures are generated or
hand-written in tmp_path — no binary fixtures are read from disk. Each test group
is skipped if its optional dependency is missing.
"""

import pathlib

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


# --- signal: tier 1 (file length) and tier 2 (checksum) --------------------- #

@pytest.fixture
def wfdb_written(tmp_path):
    """A record written by wfdb itself, so the header carries real checksums."""
    samples = np.zeros((1000, 2), dtype=np.int16)
    samples[:, 0] = np.arange(1000, dtype=np.int16)
    samples[:, 1] = 5
    wfdb.wrsamp("w", fs=250, units=["mV", "mV"], sig_name=["MLII", "V5"],
                d_signal=samples, fmt=["16", "16"],
                adc_gain=[200.0, 200.0], baseline=[0, 0], write_dir=str(tmp_path))
    return str(tmp_path / "w.hea")


def test_signal_validate_channel_count_mismatch(wfdb_written):
    """The channel set is the schema's identity and is always enforced."""
    schema = SignalSchema.infer(wfdb_written, name="w", description="d")
    del schema.properties["V5"]
    errors = schema.validate(wfdb_written)
    assert any(e.failed_keyword == "const" and e.field == "numberOfSignals"
               for e in errors)


def test_signal_schema_reused_across_recording_lengths(tmp_path, wfdb_written):
    """
    One schema, many recordings of different length: the channel set still has to
    match exactly, but a schema that does not state numberOfSamples/duration puts
    no constraint on them. Same 2 channels and rate, 1000 samples vs 250.
    """
    shorter = np.zeros((250, 2), dtype=np.int16)
    shorter[:, 0] = np.arange(250, dtype=np.int16)
    shorter[:, 1] = 5
    wfdb.wrsamp("short", fs=250, units=["mV", "mV"], sig_name=["MLII", "V5"],
                d_signal=shorter, fmt=["16", "16"],
                adc_gain=[200.0, 200.0], baseline=[0, 0], write_dir=str(tmp_path))
    other = str(tmp_path / "short.hea")

    schema = SignalSchema.infer(wfdb_written, name="two-lead-ecg", description="d")
    assert [e.field for e in schema.validate(other)] == ["numberOfSamples"]

    schema.numberOfSamples = None
    schema.duration = None
    assert schema.validate(other) == []
    assert schema.validate(other, deep=True) == []
    assert schema.validate(wfdb_written) == []  # still fits the record it came from


def test_signal_tier1_detects_truncated_dat(wfdb_written):
    """A short .dat passes every header-only check; only tier 1 sees it."""
    schema = SignalSchema.infer(wfdb_written, name="w", description="d")
    dat = pathlib.Path(wfdb_written).with_suffix(".dat")
    with open(dat, "r+b") as fh:
        fh.truncate(3000)  # 3/4 of 1000 samples x 2 channels x 2 bytes
    errors = schema.validate(wfdb_written)
    assert [e.failed_keyword for e in errors] == ["fileLength"]


def test_signal_tier1_detects_missing_dat(wfdb_written):
    schema = SignalSchema.infer(wfdb_written, name="w", description="d")
    pathlib.Path(wfdb_written).with_suffix(".dat").unlink()
    errors = schema.validate(wfdb_written)
    assert [e.failed_keyword for e in errors] == ["required"]
    assert "w.dat" in errors[0].message


def test_signal_tier2_detects_midfile_corruption(wfdb_written):
    """
    Two flipped bytes in the middle leave length and structure intact, so only
    the deep checksum tier catches them.
    """
    schema = SignalSchema.infer(wfdb_written, name="w", description="d")
    dat = pathlib.Path(wfdb_written).with_suffix(".dat")
    with open(dat, "r+b") as fh:
        fh.seek(1234)
        fh.write(b"\xff\x7f")

    assert schema.validate(wfdb_written) == []  # tier 0 + tier 1 see nothing

    errors = schema.validate(wfdb_written, deep=True)
    assert [e.failed_keyword for e in errors] == ["checksum"]
    assert errors[0].field == "V5.checksum"


def test_signal_tier2_clean_record(wfdb_written):
    schema = SignalSchema.infer(wfdb_written, name="w", description="d")
    assert validate_schema(schema, wfdb_written, deep=True) == []


def test_signal_tier2_skips_absent_checksums(tmp_path):
    """The checksum field is optional in a signal spec line; absence is not an error."""
    (tmp_path / "n.hea").write_text(
        "n 2 250 100\n"
        "n.dat 16 200(0)/mV 16 0\n"
        "n.dat 16 200(0)/mV 16 0\n"
    )
    np.zeros((100, 2), dtype="<i2").tofile(tmp_path / "n.dat")
    record = str(tmp_path / "n.hea")
    schema = SignalSchema.infer(record, name="n", description="d")
    assert schema.validate(record, deep=True) == []


def test_signal_tier1_skips_zero_length_record(tmp_path):
    (tmp_path / "z.hea").write_text(
        "z 1 250 0\n"
        "z.dat 16 200(0)/mV 16 0 0 0 0 II\n"
    )
    record = str(tmp_path / "z.hea")
    schema = SignalSchema.infer(record, name="z", description="d")
    assert schema.validate(record, deep=True) == []  # no .dat needed, none read


def test_signal_tier2_reports_decoder_disagreement(wfdb_written, monkeypatch):
    """Defensive guard: unreachable from file state, so drive it with a stub decoder."""
    schema = SignalSchema.infer(wfdb_written, name="w", description="d")
    real_rdrecord = wfdb.rdrecord

    def short_read(stem, **kwargs):
        record = real_rdrecord(stem, **kwargs)
        if kwargs.get("sampfrom") is None:
            record.e_d_signal = [record.e_d_signal[0][:500]]
        return record

    monkeypatch.setattr(wfdb, "rdrecord", short_read)
    errors = schema.validate(wfdb_written, deep=True)
    assert any(e.failed_keyword == "const" and e.field == "shape" for e in errors)
    assert any(e.field == "MLII.length" for e in errors)


def _write_bad_checksum_record(tmp_path, fmt_field):
    """1 channel, 100 zero samples (true checksum 0) but a header claiming 12345."""
    name = f"s{fmt_field.replace(':', '_')}"
    (tmp_path / f"{name}.hea").write_text(
        f"{name} 1 250 100\n"
        f"{name}.dat {fmt_field} 200(0)/mV 16 0 0 12345 0 II\n"
    )
    np.zeros((100,), dtype="<i2").tofile(tmp_path / f"{name}.dat")
    return str(tmp_path / f"{name}.hea")


def test_signal_tier2_skips_skewed_channels(tmp_path):
    """
    A skewed signal is stored time-shifted and read back aligned, so its samples
    are not the samples the header summed. Comparing would be a false positive on
    real records (MIMIC-I 03700001 RESP is 'fmt 212:4'), so the check is skipped.
    """
    skewed = _write_bad_checksum_record(tmp_path, "16:2")
    schema = SignalSchema.infer(skewed, name="skewed", description="d")
    assert schema.validate(skewed, deep=True) == []

    # Same wrong checksum without the skew field is reported, so the test above
    # is showing the skip and not just a checksum check that never runs.
    plain = _write_bad_checksum_record(tmp_path, "16")
    schema = SignalSchema.infer(plain, name="plain", description="d")
    errors = schema.validate(plain, deep=True)
    assert [e.failed_keyword for e in errors] == ["checksum"]


def test_signal_validate_reports_channel_absent_from_file(wfdb_written):
    schema = SignalSchema.infer(wfdb_written, name="w", description="d")
    schema.properties["GHOST"] = schema.properties["MLII"].model_copy(deep=True)
    errors = schema.validate(wfdb_written)
    assert any(e.failed_keyword == "required" and e.field == "GHOST" for e in errors)


def test_signal_validate_reports_undeclared_channel(wfdb_written):
    schema = SignalSchema.infer(wfdb_written, name="w", description="d")
    schema.additionalProperties = False
    del schema.properties["V5"]
    errors = schema.validate(wfdb_written)
    assert any(e.failed_keyword == "additionalProperties" and e.field == "V5"
               for e in errors)


def test_signal_infer_rejects_multisegment_record(tmp_path):
    """
    A multi-segment layout header has no signal-spec lines, so inference must say
    so rather than dying on sig_name being None (real case: MIMIC-I record 037).
    """
    (tmp_path / "m.hea").write_text("m/2 2 250 2000\ns0 1000\ns1 1000\n")
    with pytest.raises(ValueError, match="multi-segment"):
        SignalSchema.infer(str(tmp_path / "m.hea"), name="m", description="d")


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
