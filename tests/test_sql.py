from fairscape_models.utils import readCrate
from fairscape_models.
from fairscape_models.sql.conversion import (
    ConvertROCrateToSQL,
    ConvertSoftwareToSQL,
    ConvertDatasetToSQL,
    ConvertComputationToSQL
)
import pathlib

# load example data
dataversePath = pathlib.Path("/mnt/data/Dataverse")
releasePath = dataversePath / 'October2025'
cratePath = dataversePath / 'U2OS' / 'cm4ai_u2os_1_ImageDownloader.zip'

inputCrate = readCrate(cratePath)

# create test.db

def test_0_convert_0_rocrate():
    testCrateElem = inputCrate.getCrateMetadata()
    ConvertROCrateToSQL(testCrateElem)

def test_0_convert_1_dataset():
    testDatasetElem = inputCrate.getDatasets()[0]
    ConvertDatasetToSQL(testDatasetElem)
    pass

def test_0_convert_2_software():
    testSoftwareElem = inputCrate.getSoftware()[0]
    ConvertSoftwareToSQL(testSoftwareElem)
    pass

def test_0_convert_3_computation():
    testComputationElem = inputCrate.getComputations()[0]
    ConvertComputationToSQL(testComputationElem)

def test_0_convert_4_schema():
    pass

def test_1_ingest_0_rocrate():

    pass

def test_1_ingest_1_dataset():
    pass

def test_1_ingest_2_software():
    pass

def test_1_ingest_3_computation():
    pass

def test_1_ingest_4_schema():
    pass

def test_2_write_0_rocrate():
    pass

def test_2_write_1_dataset():
    pass

def test_2_write_2_software():
    pass

def test_2_write_3_computation():
    pass

def test_2_write_4_schema():
    pass


def test_3_get_0_rocrate():
    pass

def test_3_get_1_dataset():
    pass

def test_3_get_2_software():
    pass

def test_3_get_3_computation():
    pass

def test_3_get_4_schema():
    pass