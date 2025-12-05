# tests/test_rocrate_validation.py

import pytest
import pathlib
from pydantic import ValidationError
from fairscape_models.rocrate import (
    ROCrateV1_2,
    ROCrateMetadataElem,
    GenericMetadataElem,
    BioChemEntity,
    MedicalCondition
)
from fairscape_models.dataset import Dataset
from fairscape_models.software import Software
from fairscape_models.computation import Computation
from fairscape_models.mlmodel import MLModel
from fairscape_models.annotation import Annotation
from fairscape_models.experiment import Experiment

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

@pytest.fixture
def comprehensive_rocrate_data():
    """A complex ROCrate fixture to test cleaning, filtering, and validation."""
    return {
        "@context": {
            "@vocab": "https://schema.org/",
            "evi": "https://w3id.org/EVI#"
        },
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "ark:59852/comprehensive-crate"}
            },
            {
                "@id": "ark:59852/comprehensive-crate",
                "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
                "name": "Comprehensive Crate", "description": "A crate for testing.", "keywords": [],
                "isPartOf": [], "version": "1.0", "author": "tester", "license": "MIT",
                "hasPart": [
                    {"@id": "https://fairscape.net/ark:59852/test-dataset-prov"},
                    {"@id": "https://fairscape.net/ark:59852/test-software-prov"},
                    {"@id": "https://fairscape.net/ark:59852/test-computation-prov"},
                    {"@id": "ark:59852/test-biochem"},
                    {"@id": "ark:59852/test-condition"}
                ]
            },
            {
                "@id": "https://fairscape.net/ark:59852/test-dataset-prov",
                "@type": "https://w3id.org/EVI#Dataset",
                "name": "Dataset with Provenance", "author": "tester", "datePublished": "2024-01-01",
                "description": "A test dataset.", "keywords": [], "format": "text/plain",
                "usedByComputation": [{"@id": "https://fairscape.net/ark:59852/test-computation-prov"}],
                "generatedBy": [{"@id": "https://fairscape.net/ark:59852/test-computation-prov"}]
            },
            {
                "@id": "https://fairscape.net/ark:59852/test-software-prov",
                "@type": "https://w3id.org/EVI#Software",
                "name": "Software with Provenance", "author": "tester", "dateModified": "2024-01-01",
                "description": "A test software.", "format": "application/x-python",
                "usedByComputation": [{"@id": "https://fairscape.net/ark:59852/test-computation-prov"}]
            },
            {
                "@id": "https://fairscape.net/ark:59852/test-computation-prov",
                "@type": "EVI:Computation", # Test prefixed type
                "name": "Computation with Provenance", "runBy": "tester", "dateCreated": "2024-01-01",
                "description": "A test computation.",
                "usedSoftware": [{"@id": "https://fairscape.net/ark:59852/test-software-prov"}],
                "usedDataset": [{"@id": "https://fairscape.net/ark:59852/test-dataset-prov"}],
                "generated": [{"@id": "https://fairscape.net/ark:59852/test-dataset-prov"}]
            },
            {
                "@id": "ark:59852/test-biochem",
                "@type": "BioChemEntity",
                "name": "Test Protein"
            },
            {
                "@id": "ark:59852/test-condition",
                "@type": "MedicalCondition",
                "name": "Test Condition",
                "description": "A test medical condition."
            },
            {
                "@id": "ark:59852/test-other",
                "@type": "OtherEntity",
                "name": "Test Other"
            }
        ]
    }

def test_rocrate_validator_no_graph_fails():
    """Test that a crate with no @graph raises a ValidationError."""
    with pytest.raises(ValidationError, match="@graph\n  Field required"):
        ROCrateV1_2.model_validate({"@context": {}})

def test_rocrate_validator_no_type_fails():
    """Test that a graph element with no @type raises a ValueError."""
    with pytest.raises(ValueError, match="Metadata element must have @type field"):
        ROCrateV1_2.model_validate({
            "@context": {},
            "@graph": [{"@id": "test"}]
        })

def test_rocrate_validator_non_dict_in_graph_fails():
    """Test that a non-dictionary element in graph raises a ValidationError."""
    with pytest.raises(ValidationError, match="Input should be a valid dictionary"):
        ROCrateV1_2.model_validate({
            "@context": {},
            "@graph": ["a-string-in-the-graph"]
        })

def test_rocrate_validator_invalid_specific_model_fails():
    """Test that an invalid specific model raises a ValidationError."""
    # This Dataset is invalid because it's missing 'author', 'datePublished', etc.
    invalid_dataset = {
        "@id": "ark:59852/invalid-dataset",
        "@type": "Dataset",
        "name": "Invalid Dataset"
    }
    with pytest.raises(ValidationError):
        ROCrateV1_2.model_validate({
            "@context": {},
            "@graph": [invalid_dataset]
        })

def test_get_crate_metadata_no_root_node(comprehensive_rocrate_data):
    """Test that getCrateMetadata raises an exception if no root node is found."""
    # Remove the actual RO-Crate root descriptor from the graph
    comprehensive_rocrate_data["@graph"].pop(1)
    crate = ROCrateV1_2.model_validate(comprehensive_rocrate_data)
    with pytest.raises(Exception):
        crate.getCrateMetadata()

def test_clean_identifiers(comprehensive_rocrate_data):
    """Test that cleanIdentifiers correctly trims full URLs from all relevant fields."""
    rocrate = ROCrateV1_2.model_validate(comprehensive_rocrate_data)
    rocrate.cleanIdentifiers()
    
    dataset = rocrate.getDatasets()[0]
    software = rocrate.getSoftware()[0]
    computation = rocrate.getComputations()[0]

    # Check that the main guids are cleaned
    assert dataset.guid == "ark:59852/test-dataset-prov"
    assert software.guid == "ark:59852/test-software-prov"
    assert computation.guid == "ark:59852/test-computation-prov"

    # Check that provenance links are cleaned
    assert dataset.usedByComputation[0].guid == "ark:59852/test-computation-prov"
    assert dataset.generatedBy[0].guid == "ark:59852/test-computation-prov"
    assert software.usedByComputation[0].guid == "ark:59852/test-computation-prov"
    assert computation.usedSoftware[0].guid == "ark:59852/test-software-prov"
    assert computation.usedDataset[0].guid == "ark:59852/test-dataset-prov"
    assert computation.generated[0].guid == "ark:59852/test-dataset-prov"

def test_get_biochem_entities(comprehensive_rocrate_data):
    """Test filtering for BioChemEntity elements."""
    rocrate = ROCrateV1_2.model_validate(comprehensive_rocrate_data)
    entities = rocrate.getBioChemEntities()
    assert len(entities) == 1
    assert isinstance(entities[0], BioChemEntity)
    assert entities[0].guid == "ark:59852/test-biochem"

def test_get_medical_conditions(comprehensive_rocrate_data):
    """Test filtering for MedicalCondition elements."""
    rocrate = ROCrateV1_2.model_validate(comprehensive_rocrate_data)
    conditions = rocrate.getMedicalConditions()
    assert len(conditions) == 1
    assert isinstance(conditions[0], MedicalCondition)
    assert conditions[0].guid == "ark:59852/test-condition"


def test_clean_identifiers_with_none_fields():
    """Test cleanIdentifiers with None fields to ensure it doesn't crash."""
    data = {
        "@context": {},
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "ark:59852/test-crate"}
            },
            {
                "@id": "ark:59852/test-crate",
                "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
                "name": "Test Crate", "description": "A test crate for validation", "keywords": [],
                "version": "1.0", "author": "tester", "license": "MIT",
                "hasPart": [{"@id": "ark:59852/test-dataset"}]
            },
            {
                "@id": "ark:59852/test-dataset",
                "@type": "https://w3id.org/EVI#Dataset",
                "name": "Test Dataset", "author": "tester", "datePublished": "2024-01-01",
                "description": "A test dataset", "keywords": [], "format": "text/plain",
                "usedByComputation": None,  # None field
                "generatedBy": None  # None field
            }
        ]
    }
    rocrate = ROCrateV1_2.model_validate(data)
    # Should not crash
    rocrate.cleanIdentifiers()
    assert True


def test_clean_identifiers_with_single_identifier():
    """Test cleanIdentifiers with single IdentifierValue (not a list) in generatedBy."""
    data = {
        "@context": {},
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "ark:59852/test-crate"}
            },
            {
                "@id": "ark:59852/test-crate",
                "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
                "name": "Test Crate", "description": "A test crate for validation", "keywords": [],
                "version": "1.0", "author": "tester", "license": "MIT",
                "hasPart": [{"@id": "ark:59852/test-dataset"}]
            },
            {
                "@id": "https://fairscape.net/ark:59852/test-dataset",
                "@type": "https://w3id.org/EVI#Dataset",
                "name": "Test Dataset", "author": "tester", "datePublished": "2024-01-01",
                "description": "A test dataset", "keywords": [], "format": "text/plain",
                "generatedBy": {"@id": "https://fairscape.net/ark:59852/test-computation"}  # Single identifier, not list
            }
        ]
    }
    rocrate = ROCrateV1_2.model_validate(data)
    rocrate.cleanIdentifiers()
    dataset = rocrate.getDatasets()[0]
    assert dataset.generatedBy.guid == "ark:59852/test-computation"


def test_clean_identifiers_with_mlmodel():
    """Test cleanIdentifiers with MLModel elements."""
    data = {
        "@context": {},
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "ark:59852/test-crate"}
            },
            {
                "@id": "ark:59852/test-crate",
                "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
                "name": "Test Crate", "description": "A test crate for validation", "keywords": [],
                "version": "1.0", "author": "tester", "license": "MIT",
                "hasPart": [{"@id": "ark:59852/test-mlmodel"}]
            },
            {
                "@id": "https://fairscape.net/ark:59852/test-mlmodel",
                "@type": "https://w3id.org/EVI#MLModel",
                "name": "Test ML Model", "author": "tester", "datePublished": "2024-01-01",
                "description": "A test ML model", "format": "application/x-hdf5",
                "usedByComputation": [{"@id": "https://fairscape.net/ark:59852/test-computation"}],
                "trainedOn": [{"@id": "https://fairscape.net/ark:59852/test-dataset"}]
            }
        ]
    }
    rocrate = ROCrateV1_2.model_validate(data)
    rocrate.cleanIdentifiers()
    mlmodel = rocrate.getMLModels()[0]
    assert mlmodel.guid == "ark:59852/test-mlmodel"
    assert mlmodel.usedByComputation[0].guid == "ark:59852/test-computation"
    assert mlmodel.trainedOn[0].guid == "ark:59852/test-dataset"


def test_clean_identifiers_with_annotation():
    """Test cleanIdentifiers with Annotation elements."""
    data = {
        "@context": {},
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "ark:59852/test-crate"}
            },
            {
                "@id": "ark:59852/test-crate",
                "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
                "name": "Test Crate", "description": "A test crate for validation", "keywords": [],
                "version": "1.0", "author": "tester", "license": "MIT",
                "hasPart": [{"@id": "ark:59852/test-annotation"}]
            },
            {
                "@id": "https://fairscape.net/ark:59852/test-annotation",
                "@type": "https://w3id.org/EVI#Annotation",
                "name": "Test Annotation", "author": "tester", "dateCreated": "2024-01-01",
                "description": "A test annotation",
                "createdBy": "tester",
                "usedDataset": [{"@id": "https://fairscape.net/ark:59852/test-dataset"}],
                "generated": [{"@id": "https://fairscape.net/ark:59852/test-output"}]
            }
        ]
    }
    rocrate = ROCrateV1_2.model_validate(data)
    rocrate.cleanIdentifiers()
    annotation = rocrate.getAnnotations()[0]
    assert annotation.guid == "ark:59852/test-annotation"
    assert annotation.usedDataset[0].guid == "ark:59852/test-dataset"
    assert annotation.generated[0].guid == "ark:59852/test-output"


def test_clean_identifiers_with_experiment():
    """Test cleanIdentifiers with Experiment elements."""
    data = {
        "@context": {},
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "ark:59852/test-crate"}
            },
            {
                "@id": "ark:59852/test-crate",
                "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
                "name": "Test Crate", "description": "A test crate for validation", "keywords": [],
                "version": "1.0", "author": "tester", "license": "MIT",
                "hasPart": [{"@id": "ark:59852/test-experiment"}]
            },
            {
                "@id": "https://fairscape.net/ark:59852/test-experiment",
                "@type": "https://w3id.org/EVI#Experiment",
                "name": "Test Experiment", "author": "tester", "dateCreated": "2024-01-01",
                "description": "A test experiment",
                "experimentType": "microscopy",
                "runBy": "tester",
                "datePerformed": "2024-01-01",
                "usedInstrument": [{"@id": "https://fairscape.net/ark:59852/test-instrument"}],
                "usedSample": [{"@id": "https://fairscape.net/ark:59852/test-sample"}],
                "usedTreatment": [{"@id": "https://fairscape.net/ark:59852/test-treatment"}],
                "usedStain": [{"@id": "https://fairscape.net/ark:59852/test-stain"}],
                "generated": [{"@id": "https://fairscape.net/ark:59852/test-result"}]
            }
        ]
    }
    rocrate = ROCrateV1_2.model_validate(data)
    rocrate.cleanIdentifiers()
    experiment = rocrate.getExperiments()[0]
    assert experiment.guid == "ark:59852/test-experiment"
    assert experiment.usedInstrument[0].guid == "ark:59852/test-instrument"
    assert experiment.usedSample[0].guid == "ark:59852/test-sample"
    assert experiment.usedTreatment[0].guid == "ark:59852/test-treatment"
    assert experiment.usedStain[0].guid == "ark:59852/test-stain"
    assert experiment.generated[0].guid == "ark:59852/test-result"