import pytest
from pydantic import ValidationError
from fairscape_models.schema import Schema, Property

@pytest.fixture
def property_data():
    return {
        "description": "A test property",
        "index": 1,
        "type": "string",
        "value-url": "http://example.com/value"
    }

def test_property_instantiation(property_data):
    prop = Property.model_validate(property_data)
    assert prop.description == "A test property"
    assert prop.index == 1
    assert prop.value_url == "http://example.com/value"

def test_property_invalid_type(property_data):
    property_data["type"] = "invalid_type"
    with pytest.raises(ValueError, match="Type must be one of"):
        Property.model_validate(property_data)

def test_property_invalid_index_string(property_data):
    property_data["index"] = "invalid::string"
    with pytest.raises(ValueError, match="Index must match the pattern"):
        Property.model_validate(property_data)

def test_property_valid_index_string(property_data):
    property_data["index"] = "1::2"
    prop = Property.model_validate(property_data)
    assert prop.index == "1::2"

def test_schema_instantiation():
    schema_data = {
        "@id": "ark:59852/test-schema",
        "@type": "evi:Schema",
        "name": "Test Schema",
        "description": "A basic test schema.",
        "properties": {
            "col1": {
                "description": "Column 1",
                "index": 0,
                "type": "string"
            }
        }
    }
    schema_obj = Schema.model_validate(schema_data)
    assert schema_obj.guid == "ark:59852/test-schema"
    assert "col1" in schema_obj.properties

def test_property_pattern_validation(property_data):
    """
    Tests the regex validation for the 'pattern' field in the Property model.
    """
    # Case 1: Pattern is None (default), which should be valid.
    prop_none = Property.model_validate(property_data)
    assert prop_none.pattern is None

    # Case 2: A valid regex pattern is provided.
    valid_data = property_data.copy()
    valid_data['pattern'] = '^[a-zA-Z0-9_-]+$'
    prop_valid = Property.model_validate(valid_data)
    assert prop_valid.pattern == '^[a-zA-Z0-9_-]+$'

    # Case 3: An invalid regex pattern (e.g., an unclosed bracket) is provided.
    # This should raise a ValueError with the specific message from the validator.
    invalid_data = property_data.copy()
    invalid_data['pattern'] = '['
    with pytest.raises(ValueError, match="Pattern must be a valid regular expression"):
        Property.model_validate(invalid_data)