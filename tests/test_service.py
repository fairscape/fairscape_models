import pytest
from pydantic import ValidationError
from fairscape_models.service import Service
from fairscape_models.fairscape_base import SERVICE_TYPE, IdentifierValue


@pytest.fixture
def service_minimal_data():
    return {
        "@id": "ark:59852/test-service",
        "name": "Test Service",
        "description": "A service that does useful things on demand.",
    }


def test_service_instantiation(service_minimal_data):
    service = Service.model_validate(service_minimal_data)
    assert service.guid == service_minimal_data["@id"]
    assert service.name == service_minimal_data["name"]
    assert service.metadataType == ["prov:SoftwareAgent", "https://w3id.org/EVI#Service"]


def test_service_short_description(service_minimal_data):
    service_minimal_data["description"] = "short"
    with pytest.raises(ValidationError):
        Service.model_validate(service_minimal_data)


def test_service_with_optional_fields(service_minimal_data):
    service_minimal_data["serviceUrl"] = "https://example.org/svc"
    service_minimal_data["associatedPublication"] = "doi:10.1/x"
    service_minimal_data["additionalDocumentation"] = "https://example.org/docs"
    service_minimal_data["usedByComputation"] = [{"@id": "ark:59852/comp-1"}]
    service_minimal_data["isPartOf"] = [{"@id": "ark:59852/crate-1"}]
    service = Service.model_validate(service_minimal_data)
    assert service.serviceUrl == "https://example.org/svc"
    assert isinstance(service.usedByComputation[0], IdentifierValue)
    assert isinstance(service.isPartOf[0], IdentifierValue)


def test_service_missing_required_field(service_minimal_data):
    del service_minimal_data["name"]
    with pytest.raises(ValidationError):
        Service.model_validate(service_minimal_data)


def test_service_type_constant():
    assert SERVICE_TYPE == "Service"
