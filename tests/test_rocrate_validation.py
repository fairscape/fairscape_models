# tests/test_rocrate_validation.py

import pytest
import pathlib
from pydantic import ValidationError
from fairscape_models.rocrate import (
    ROCrateV1_2,
    ROCrateMetadataElem,
    GenericMetadataElem,
    BioChemEntity,
    MedicalCondition,
    IRB,
    ContactPoint,
    PostalAddress,
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


def _minimal_rocrate_elem(**kwargs) -> ROCrateMetadataElem:
    """Build a minimal ROCrateMetadataElem, overridable via kwargs."""
    base = {
        "@id": "ark:59852/test-crate",
        "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
        "name": "Test", "description": "Test", "keywords": [],
        "version": "1.0", "author": "tester", "license": None,
        "hasPart": []
    }
    base.update(kwargs)
    return ROCrateMetadataElem.model_validate(base)


def test_get_aiready_warnings_all_missing():
    """All recommended fields absent → all 9 warnings returned."""
    elem = _minimal_rocrate_elem()
    warnings = elem.get_aiready_warnings()
    assert len(warnings) == 11
    texts = "\n".join(warnings)
    assert "identifier" in texts
    assert "license" in texts
    assert "publisher" in texts
    assert "rai:dataBiases" in texts
    assert "rai:dataCollectionMissingData" in texts
    assert "contentSize" in texts
    assert "rai:dataUseCases" in texts
    assert "rai:dataCollection" in texts
    assert "ethicalReview" in texts
    assert "confidentialityLevel" in texts
    assert "rai:dataReleaseMaintenancePlan" in texts


def test_get_aiready_warnings_all_present():
    """All recommended fields present → empty warnings list."""
    elem = _minimal_rocrate_elem(**{
        "identifier": "https://doi.org/10.1234/test",
        "license": "MIT",
        "publisher": "Test Publisher",
        "rai:dataBiases": "None known",
        "rai:dataCollectionMissingData": "No missing data",
        "contentSize": "1GB",
        "rai:dataUseCases": "Training ML models",
        "rai:dataCollection": "Prospective study",
        "ethicalReview": "IRB approved",
        "confidentialityLevel": "Public",
        "rai:dataReleaseMaintenancePlan": "Annual updates",
    })
    warnings = elem.get_aiready_warnings()
    assert warnings == []


def test_get_aiready_warnings_partial():
    """publisher present suppresses that warning; others still fire."""
    elem = _minimal_rocrate_elem(publisher="UCSD")
    warnings = elem.get_aiready_warnings()
    texts = "\n".join(warnings)
    assert "publisher" not in texts
    assert "identifier" in texts


def test_get_aiready_warnings_missing_license():
    """No license → license warning fires."""
    elem = _minimal_rocrate_elem(**{"license": None})
    warnings = elem.get_aiready_warnings()
    texts = "\n".join(warnings)
    assert "license" in texts


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


# ── IRB class tests ─────────────────────────────────────────────────────

class TestContactPoint:
    """Tests for the ContactPoint model."""

    def test_defaults(self):
        cp = ContactPoint()
        assert cp.metadataType == "ContactPoint"
        assert cp.contactType is None
        assert cp.email is None
        assert cp.telephone is None

    def test_full(self):
        cp = ContactPoint(
            contactType="IRB Reliance and Compliance",
            email="irbreliance@mgb.org",
            telephone="+1-857-282-1900",
        )
        assert cp.contactType == "IRB Reliance and Compliance"
        assert cp.email == "irbreliance@mgb.org"
        assert cp.telephone == "+1-857-282-1900"

    def test_alias_serialization(self):
        cp = ContactPoint(email="test@example.com")
        dumped = cp.model_dump(by_alias=True)
        assert dumped["@type"] == "ContactPoint"
        assert "metadataType" not in dumped

    def test_from_dict_with_alias(self):
        cp = ContactPoint.model_validate({
            "@type": "ContactPoint",
            "email": "test@example.com",
        })
        assert cp.metadataType == "ContactPoint"
        assert cp.email == "test@example.com"

    def test_extra_fields_allowed(self):
        cp = ContactPoint.model_validate({
            "email": "test@example.com",
            "url": "https://example.com",
        })
        assert cp.email == "test@example.com"


class TestPostalAddress:
    """Tests for the PostalAddress model."""

    def test_defaults(self):
        addr = PostalAddress()
        assert addr.metadataType == "PostalAddress"
        assert addr.streetAddress is None
        assert addr.addressLocality is None
        assert addr.addressRegion is None
        assert addr.postalCode is None
        assert addr.addressCountry is None

    def test_full(self):
        addr = PostalAddress(
            streetAddress="399 Revolution Drive, Suite 710",
            addressLocality="Somerville",
            addressRegion="MA",
            postalCode="02145",
            addressCountry="US",
        )
        assert addr.streetAddress == "399 Revolution Drive, Suite 710"
        assert addr.addressLocality == "Somerville"
        assert addr.addressRegion == "MA"
        assert addr.postalCode == "02145"
        assert addr.addressCountry == "US"

    def test_alias_serialization(self):
        addr = PostalAddress(addressLocality="Boston")
        dumped = addr.model_dump(by_alias=True)
        assert dumped["@type"] == "PostalAddress"

    def test_from_dict_with_alias(self):
        addr = PostalAddress.model_validate({
            "@type": "PostalAddress",
            "addressLocality": "Boston",
            "addressRegion": "MA",
        })
        assert addr.addressLocality == "Boston"
        assert addr.addressRegion == "MA"


class TestIRB:
    """Tests for the IRB model."""

    def test_minimal(self):
        irb = IRB(name="Test IRB")
        assert irb.metadataType == "IRB"
        assert irb.name == "Test IRB"
        assert irb.contactPoint is None
        assert irb.address is None

    def test_name_required(self):
        with pytest.raises(ValidationError, match="name"):
            IRB.model_validate({})

    def test_full_mgb_irb(self):
        """Full MGB IRB example from requirements."""
        irb = IRB(
            name="Mass General Brigham Institutional Review Board (MGB IRB)",
            contactPoint=ContactPoint(
                contactType="IRB Reliance and Compliance",
                email="irbreliance@mgb.org",
                telephone="+1-857-282-1900",
            ),
            address=PostalAddress(
                streetAddress="399 Revolution Drive, Suite 710",
                addressLocality="Somerville",
                addressRegion="MA",
                postalCode="02145",
                addressCountry="US",
            ),
        )
        assert irb.name == "Mass General Brigham Institutional Review Board (MGB IRB)"
        assert irb.contactPoint.email == "irbreliance@mgb.org"
        assert irb.contactPoint.telephone == "+1-857-282-1900"
        assert irb.contactPoint.contactType == "IRB Reliance and Compliance"
        assert irb.address.streetAddress == "399 Revolution Drive, Suite 710"
        assert irb.address.addressLocality == "Somerville"
        assert irb.address.postalCode == "02145"

    def test_alias_serialization(self):
        irb = IRB(name="Test IRB")
        dumped = irb.model_dump(by_alias=True)
        assert dumped["@type"] == "IRB"
        assert dumped["name"] == "Test IRB"

    def test_from_dict_with_alias(self):
        irb = IRB.model_validate({
            "@type": "IRB",
            "name": "Test IRB",
            "contactPoint": {
                "@type": "ContactPoint",
                "email": "test@example.com",
            },
        })
        assert irb.name == "Test IRB"
        assert irb.contactPoint.email == "test@example.com"

    def test_nested_roundtrip(self):
        """Serialize to dict and back — full nested structure survives."""
        irb = IRB(
            name="MGB IRB",
            contactPoint=ContactPoint(email="irb@mgb.org", telephone="+1-555-0100"),
            address=PostalAddress(addressLocality="Somerville", addressRegion="MA"),
        )
        dumped = irb.model_dump(by_alias=True)
        restored = IRB.model_validate(dumped)
        assert restored.name == irb.name
        assert restored.contactPoint.email == irb.contactPoint.email
        assert restored.contactPoint.telephone == irb.contactPoint.telephone
        assert restored.address.addressLocality == irb.address.addressLocality
        assert restored.address.addressRegion == irb.address.addressRegion

    def test_extra_fields_allowed(self):
        irb = IRB.model_validate({
            "name": "Test IRB",
            "irbNumber": "IRB-2024-001",
        })
        assert irb.name == "Test IRB"


class TestROCrateMetadataElemIRB:
    """Tests for IRB as a property on ROCrateMetadataElem."""

    def test_irb_as_string(self):
        elem = _minimal_rocrate_elem(irb="MGB IRB")
        assert elem.irb == "MGB IRB"

    def test_irb_as_none(self):
        elem = _minimal_rocrate_elem()
        assert elem.irb is None

    def test_irb_as_structured_class(self):
        elem = _minimal_rocrate_elem(irb={
            "@type": "IRB",
            "name": "Mass General Brigham IRB",
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "IRB Reliance and Compliance",
                "email": "irbreliance@mgb.org",
                "telephone": "+1-857-282-1900",
            },
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "399 Revolution Drive, Suite 710",
                "addressLocality": "Somerville",
                "addressRegion": "MA",
                "postalCode": "02145",
                "addressCountry": "US",
            },
        })
        assert isinstance(elem.irb, IRB)
        assert elem.irb.name == "Mass General Brigham IRB"
        assert elem.irb.contactPoint.email == "irbreliance@mgb.org"
        assert elem.irb.address.addressLocality == "Somerville"

    def test_irb_structured_serialization(self):
        """Structured IRB round-trips through ROCrateMetadataElem."""
        elem = _minimal_rocrate_elem(irb={
            "@type": "IRB",
            "name": "Test IRB",
            "contactPoint": {"@type": "ContactPoint", "email": "irb@test.edu"},
        })
        dumped = elem.model_dump(by_alias=True)
        irb_data = dumped["irb"]
        assert irb_data["@type"] == "IRB"
        assert irb_data["name"] == "Test IRB"
        assert irb_data["contactPoint"]["email"] == "irb@test.edu"

    def test_irb_string_serialization(self):
        """String IRB round-trips through ROCrateMetadataElem."""
        elem = _minimal_rocrate_elem(irb="Simple IRB Name")
        dumped = elem.model_dump(by_alias=True)
        assert dumped["irb"] == "Simple IRB Name"

    def test_irb_in_full_rocrate(self):
        """IRB class works inside a full ROCrate validation."""
        data = {
            "@context": {},
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                    "about": {"@id": "ark:59852/irb-crate"},
                },
                {
                    "@id": "ark:59852/irb-crate",
                    "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
                    "name": "IRB Test Crate",
                    "description": "Crate with structured IRB",
                    "keywords": [],
                    "version": "1.0",
                    "author": "tester",
                    "license": "MIT",
                    "hasPart": [],
                    "irb": {
                        "@type": "IRB",
                        "name": "MGB IRB",
                        "contactPoint": {
                            "@type": "ContactPoint",
                            "email": "irb@mgb.org",
                        },
                    },
                    "irbProtocolId": "2024-P000123",
                },
            ],
        }
        rocrate = ROCrateV1_2.model_validate(data)
        meta = rocrate.getCrateMetadata()
        assert isinstance(meta.irb, IRB)
        assert meta.irb.name == "MGB IRB"
        assert meta.irb.contactPoint.email == "irb@mgb.org"
        assert meta.irbProtocolId == "2024-P000123"

    def test_irb_string_in_full_rocrate(self):
        """String IRB still works inside a full ROCrate."""
        data = {
            "@context": {},
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                    "about": {"@id": "ark:59852/irb-crate"},
                },
                {
                    "@id": "ark:59852/irb-crate",
                    "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
                    "name": "IRB Test Crate",
                    "description": "Crate with string IRB",
                    "keywords": [],
                    "version": "1.0",
                    "author": "tester",
                    "license": "MIT",
                    "hasPart": [],
                    "irb": "Mass General Brigham IRB",
                },
            ],
        }
        rocrate = ROCrateV1_2.model_validate(data)
        meta = rocrate.getCrateMetadata()
        assert meta.irb == "Mass General Brigham IRB"