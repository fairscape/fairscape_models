"""DICOM image schema infer/validate. Skipped without the schema-image extra."""

import pytest

from fairscape_models.schema import ImageSchema, infer_schema, validate_schema

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
