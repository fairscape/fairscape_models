import pytest

@pytest.fixture
def dataset_minimal_data():
    """Minimal data for a valid Dataset."""
    return {
        "@id": "ark:59852/test-dataset",
        "name": "Test Dataset",
        "author": "Test Author",
        "datePublished": "2023-11-09",
        "description": "This is a test dataset with sufficient description.",
        "keywords": ["test", "dataset"],
        "format": "text/csv"
    }

@pytest.fixture
def software_minimal_data():
    """Minimal data for a valid Software."""
    return {
        "@id": "ark:59852/test-software",
        "name": "Test Software",
        "author": "Test Author",
        "dateModified": "2023-11-09",
        "description": "This is a test software with a good description.",
        "format": "application/x-python"
    }

@pytest.fixture
def computation_minimal_data():
    """Minimal data for a valid Computation."""
    return {
        "@id": "ark:59852/test-computation",
        "name": "Test Computation",
        "runBy": "Test Runner",
        "dateCreated": "2023-11-09",
        "description": "A test computation description that is long enough."
    }
    
@pytest.fixture
def instrument_minimal_data():
    """Minimal data for a valid Instrument."""
    return {
        "@id": "ark:59852/test-instrument",
        "name": "Test Instrument",
        "manufacturer": "Test-O-Matic Inc.",
        "model": "Z-1000",
        "description": "A test instrument for science."
    }

@pytest.fixture
def experiment_minimal_data():
    """Minimal data for a valid Experiment."""
    return {
        "@id": "ark:59852/test-experiment",
        "name": "Test Experiment",
        "experimentType": "Microscopy",
        "runBy": "Dr. Tester",
        "description": "An experiment to test things.",
        "datePerformed": "2024-01-01"
    }