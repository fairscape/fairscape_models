import pytest
from pydantic import ValidationError
from fairscape_models.container import Container
from fairscape_models.fairscape_base import CONTAINER_TYPE, IdentifierValue


@pytest.fixture
def container_minimal_data():
    return {
        "@id": "ark:59852/test-container",
        "name": "Test Container",
        "author": "Test Author",
        "description": "A container of digital objects for testing purposes.",
    }


def test_container_instantiation(container_minimal_data):
    container = Container.model_validate(container_minimal_data)
    assert container.guid == container_minimal_data["@id"]
    assert container.additionalType == CONTAINER_TYPE
    assert container.metadataType == ["prov:Entity", "https://w3id.org/EVI#Container"]
    assert container.wasAttributedTo == ["Test Author"]


def test_container_multiple_authors(container_minimal_data):
    container_minimal_data["author"] = ["Author 1", "Author 2"]
    container = Container.model_validate(container_minimal_data)
    assert container.wasAttributedTo == ["Author 1", "Author 2"]


def test_container_empty_author(container_minimal_data):
    container_minimal_data["author"] = []
    container = Container.model_validate(container_minimal_data)
    assert container.wasAttributedTo == []


def test_container_with_packages(container_minimal_data):
    container_minimal_data["evi:packages"] = [{"@id": "ark:59852/pkg-1"}]
    container = Container.model_validate(container_minimal_data)
    assert len(container.packages) == 1
    assert isinstance(container.packages[0], IdentifierValue)
    assert container.packages[0].guid == "ark:59852/pkg-1"


def test_container_missing_required_field(container_minimal_data):
    del container_minimal_data["name"]
    with pytest.raises(ValidationError):
        Container.model_validate(container_minimal_data)
