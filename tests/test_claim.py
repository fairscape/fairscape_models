import pytest
from pydantic import ValidationError
from fairscape_models.claim import Claim
from fairscape_models.fairscape_base import CLAIM_TYPE, IdentifierValue


@pytest.fixture
def claim_minimal_data():
    return {
        "@id": "ark:59852/test-claim",
        "name": "Test Claim",
        "author": "Test Author",
        "description": "A claim describing something important.",
        "evi:state": "This is the textual representation of the claim.",
    }


def test_claim_instantiation(claim_minimal_data):
    claim = Claim.model_validate(claim_minimal_data)
    assert claim.guid == claim_minimal_data["@id"]
    assert claim.claimText == claim_minimal_data["evi:state"]
    assert claim.additionalType == CLAIM_TYPE
    assert claim.metadataType == ["prov:Entity", "https://w3id.org/EVI#Claim"]
    assert claim.wasAttributedTo == ["Test Author"]


def test_claim_multiple_authors(claim_minimal_data):
    claim_minimal_data["author"] = ["Author 1", "Author 2"]
    claim = Claim.model_validate(claim_minimal_data)
    assert claim.wasAttributedTo == ["Author 1", "Author 2"]


def test_claim_empty_author(claim_minimal_data):
    claim_minimal_data["author"] = []
    claim = Claim.model_validate(claim_minimal_data)
    assert claim.wasAttributedTo == []


def test_claim_with_supported_by(claim_minimal_data):
    claim_minimal_data["supportedBy"] = [{"@id": "ark:59852/article-1"}]
    claim = Claim.model_validate(claim_minimal_data)
    assert len(claim.supportedBy) == 1
    assert isinstance(claim.supportedBy[0], IdentifierValue)
    assert claim.supportedBy[0].guid == "ark:59852/article-1"


def test_claim_missing_required_field(claim_minimal_data):
    del claim_minimal_data["evi:state"]
    with pytest.raises(ValidationError):
        Claim.model_validate(claim_minimal_data)
