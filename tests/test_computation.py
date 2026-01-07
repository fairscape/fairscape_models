import pytest
from pydantic import ValidationError
from fairscape_models.computation import Computation
from fairscape_models.fairscape_base import IdentifierValue

def test_computation_instantiation(computation_minimal_data):
    """Test successful instantiation of a Computation model."""
    computation = Computation.model_validate(computation_minimal_data)
    assert computation.guid == computation_minimal_data["@id"]
    assert computation.description == computation_minimal_data["description"]

    # Test PROV field auto-population
    assert computation.used == []  # No inputs provided
    assert len(computation.wasAssociatedWith) == 1
    assert computation.wasAssociatedWith[0] == computation_minimal_data["runBy"]

def test_computation_short_description(computation_minimal_data):
    """Test that a short description raises a ValidationError."""
    computation_minimal_data["description"] = "too short"
    with pytest.raises(ValidationError):
        Computation.model_validate(computation_minimal_data)

def test_computation_with_inputs(computation_minimal_data):
    """Test PROV field population with usedSoftware, usedDataset, usedMLModel."""
    computation_minimal_data["usedSoftware"] = [{"@id": "ark:59852/software-1"}]
    computation_minimal_data["usedDataset"] = [{"@id": "ark:59852/dataset-1"}]
    computation_minimal_data["usedMLModel"] = [{"@id": "ark:59852/model-1"}]

    computation = Computation.model_validate(computation_minimal_data)

    # Test PROV:used aggregates all inputs
    assert len(computation.used) == 3
    assert all(isinstance(item, IdentifierValue) for item in computation.used)
    used_ids = [item.guid for item in computation.used]
    assert "ark:59852/software-1" in used_ids
    assert "ark:59852/dataset-1" in used_ids
    assert "ark:59852/model-1" in used_ids

