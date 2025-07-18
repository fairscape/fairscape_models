import pytest
from pydantic import ValidationError
from fairscape_models.computation import Computation

def test_computation_instantiation(computation_minimal_data):
    """Test successful instantiation of a Computation model."""
    computation = Computation.model_validate(computation_minimal_data)
    assert computation.guid == computation_minimal_data["@id"]
    assert computation.description == computation_minimal_data["description"]

def test_computation_short_description(computation_minimal_data):
    """Test that a short description raises a ValidationError."""
    computation_minimal_data["description"] = "too short"
    with pytest.raises(ValidationError):
        Computation.model_validate(computation_minimal_data)