import pytest
from pydantic import ValidationError
from fairscape_models.experiment import Experiment
from fairscape_models.fairscape_base import IdentifierValue

def test_experiment_instantiation(experiment_minimal_data):
    """Test successful instantiation of an Experiment model."""
    experiment = Experiment.model_validate(experiment_minimal_data)
    assert experiment.guid == experiment_minimal_data["@id"]
    assert experiment.name == experiment_minimal_data["name"]
    assert experiment.experimentType == experiment_minimal_data["experimentType"]

    # Test PROV field auto-population
    assert experiment.used == []  # No used items provided
    assert len(experiment.wasAssociatedWith) == 1
    assert experiment.wasAssociatedWith[0] == experiment_minimal_data["runBy"]

def test_experiment_missing_required_field(experiment_minimal_data):
    """Test that a ValidationError is raised for a missing required field."""
    del experiment_minimal_data["runBy"]
    with pytest.raises(ValidationError):
        Experiment.model_validate(experiment_minimal_data)

def test_experiment_short_description(experiment_minimal_data):
    """Test that a short description raises a ValidationError."""
    experiment_minimal_data["description"] = "too short"
    with pytest.raises(ValidationError):
        Experiment.model_validate(experiment_minimal_data)

def test_experiment_with_used_items(experiment_minimal_data):
    """Test instantiation with various 'used' lists."""
    instrument_id = {"@id": "ark:59852/inst-1"}
    sample_id = {"@id": "ark:59852/sample-1"}

    experiment_minimal_data["usedInstrument"] = [instrument_id]
    experiment_minimal_data["usedSample"] = [sample_id]

    experiment = Experiment.model_validate(experiment_minimal_data)

    assert isinstance(experiment.usedInstrument[0], IdentifierValue)
    assert experiment.usedInstrument[0].guid == instrument_id["@id"]
    assert isinstance(experiment.usedSample[0], IdentifierValue)
    assert experiment.usedSample[0].guid == sample_id["@id"]

    # Test PROV:used aggregates all inputs
    assert len(experiment.used) == 2
    assert all(isinstance(item, IdentifierValue) for item in experiment.used)
    used_ids = [item.guid for item in experiment.used]
    assert "ark:59852/inst-1" in used_ids
    assert "ark:59852/sample-1" in used_ids