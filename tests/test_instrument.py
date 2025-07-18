import pytest
from pydantic import ValidationError
from fairscape_models.instrument import Instrument
from fairscape_models.fairscape_base import IdentifierValue

def test_instrument_instantiation(instrument_minimal_data):
    """Test successful instantiation of an Instrument model."""
    instrument = Instrument.model_validate(instrument_minimal_data)
    assert instrument.guid == instrument_minimal_data["@id"]
    assert instrument.name == instrument_minimal_data["name"]
    assert instrument.manufacturer == instrument_minimal_data["manufacturer"]

def test_instrument_missing_required_field(instrument_minimal_data):
    """Test that a ValidationError is raised for a missing required field."""
    del instrument_minimal_data["model"]
    with pytest.raises(ValidationError):
        Instrument.model_validate(instrument_minimal_data)

def test_instrument_short_manufacturer(instrument_minimal_data):
    """Test that a short manufacturer name raises a ValidationError."""
    instrument_minimal_data["manufacturer"] = "abc"
    with pytest.raises(ValidationError):
        Instrument.model_validate(instrument_minimal_data)

def test_instrument_with_used_by(instrument_minimal_data):
    """Test instantiation with a usedByExperiment list."""
    exp_id = {"@id": "ark:59852/exp-1"}
    instrument_minimal_data["usedByExperiment"] = [exp_id]
    instrument = Instrument.model_validate(instrument_minimal_data)
    assert isinstance(instrument.usedByExperiment[0], IdentifierValue)
    assert instrument.usedByExperiment[0].guid == exp_id["@id"]