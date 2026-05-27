import pytest
from pydantic import ValidationError
from fairscape_models.article import Article
from fairscape_models.fairscape_base import ARTICLE_TYPE, IdentifierValue


@pytest.fixture
def article_minimal_data():
    return {
        "@id": "ark:59852/test-article",
        "name": "Test Article",
        "author": "Test Author",
        "description": "An article about testing things in great detail.",
    }


def test_article_instantiation(article_minimal_data):
    article = Article.model_validate(article_minimal_data)
    assert article.guid == article_minimal_data["@id"]
    assert article.name == article_minimal_data["name"]
    assert article.additionalType == ARTICLE_TYPE
    assert article.metadataType == ["prov:Entity", "https://w3id.org/EVI#Article"]
    assert article.wasAttributedTo == ["Test Author"]


def test_article_multiple_authors(article_minimal_data):
    article_minimal_data["author"] = ["Author 1", "Author 2"]
    article = Article.model_validate(article_minimal_data)
    assert article.wasAttributedTo == ["Author 1", "Author 2"]


def test_article_empty_author(article_minimal_data):
    article_minimal_data["author"] = []
    article = Article.model_validate(article_minimal_data)
    assert article.wasAttributedTo == []


def test_article_with_optional_fields(article_minimal_data):
    article_minimal_data["datePublished"] = "2024-01-01"
    article_minimal_data["keywords"] = ["k1", "k2"]
    article_minimal_data["hasPart"] = [{"@id": "ark:59852/claim-1"}]
    article = Article.model_validate(article_minimal_data)
    assert article.datePublished == "2024-01-01"
    assert article.keywords == ["k1", "k2"]
    assert len(article.hasPart) == 1
    assert isinstance(article.hasPart[0], IdentifierValue)


def test_article_missing_required_field(article_minimal_data):
    del article_minimal_data["name"]
    with pytest.raises(ValidationError):
        Article.model_validate(article_minimal_data)
