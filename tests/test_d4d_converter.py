from fairscape_models.rocrate import ROCrateV1_2
from fairscape_models.conversion.d4d_converter import D4DConverter
import pytest
import pathlib


# Define the path to the Test-ROcrates directory
TEST_ROCRATES_PATH = pathlib.Path(__file__).parent / "test_rocrates"

def find_rocrate_metadata_files(base_path: pathlib.Path):
    """Recursively finds all ro-crate-metadata.json files."""
    if not base_path.is_dir():
        return []
    return list(base_path.rglob("ro-crate-metadata.json"))


# Create a list of test cases for parametrization
test_files = find_rocrate_metadata_files(TEST_ROCRATES_PATH)
test_ids = [str(p.relative_to(TEST_ROCRATES_PATH)) for p in test_files]


@pytest.mark.parametrize("rocrate_file_path", test_files, ids=test_ids)
def test_validate_test_rocrates(rocrate_file_path: pathlib.Path):
    """Parametrized test to validate all ro-crate-metadata.json files."""
    print(f"\n--> Validating Test-ROCrate: {rocrate_file_path.relative_to(TEST_ROCRATES_PATH)}")
    
    with open(rocrate_file_path, 'r', encoding='utf-8') as f:
        rocrate_json_data = f.read()

    rocrate_instance = ROCrateV1_2.model_validate_json(rocrate_json_data)
    
    assert rocrate_instance is not None
    assert isinstance(rocrate_instance, ROCrateV1_2)

    # convert d4d test
    genD4D = D4DConverter(rocrate_instance)

    genD4D.convert()

    assert genD4D.d4dOutput is not None
    assert isinstance(genD4D.d4dOutput, dict)

    