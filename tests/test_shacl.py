# tests/test_shacl.py

import json
import pathlib

import pytest

pytest.importorskip("pyshacl")

from fairscape_models.rocrate import ROCrateV1_2
from fairscape_models.validation.shacl import (
    default_shapes_path,
    resolve_metadata_path,
    validate_shacl,
)

TEST_ROCRATES_PATH = pathlib.Path(__file__).parent / "test_rocrates"
LAKEDB = TEST_ROCRATES_PATH / "LakeDB"
RELEASE = TEST_ROCRATES_PATH / "release"


def test_bundled_shapes_ship_with_package():
    assert default_shapes_path().is_file()


def test_resolve_metadata_path():
    assert resolve_metadata_path(LAKEDB) == LAKEDB / "ro-crate-metadata.json"
    assert resolve_metadata_path(LAKEDB / "ro-crate-metadata.json") == LAKEDB / "ro-crate-metadata.json"


@pytest.mark.parametrize("crate_dir", [LAKEDB, RELEASE], ids=["LakeDB", "release"])
def test_fixture_crates_pass(crate_dir):
    report = validate_shacl(crate_dir)
    assert report.passes, [r for r in report.results if r.severity == "Violation"]
    assert report.violations == 0


def test_accepts_dict_and_model():
    data = json.loads((LAKEDB / "ro-crate-metadata.json").read_text())
    assert validate_shacl(data).passes
    assert validate_shacl(ROCrateV1_2.model_validate(data)).passes


def test_warnings_do_not_fail():
    # LakeDB references ark: nodes it doesn't describe, which the profile
    # reports as an advisory sh:Warning.
    report = validate_shacl(LAKEDB)
    assert report.warnings >= 1
    assert report.passes


def test_dataset_without_author_is_a_violation():
    data = json.loads((LAKEDB / "ro-crate-metadata.json").read_text())
    dataset_id = "ark:59852/dataset-input-patient-data-qt7fpva3pt"
    for entity in data["@graph"]:
        if entity["@id"] == dataset_id:
            entity.pop("author")

    report = validate_shacl(data)
    assert not report.passes
    violation = next(r for r in report.results if r.severity == "Violation")
    assert violation.shape == "DatasetAuthorShape"
    assert violation.focusNode == dataset_id
    assert violation.path == "https://schema.org/author"
