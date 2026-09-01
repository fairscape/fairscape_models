from fairscape_models.sql.models import (
    ROCrateMetadataElemSQL,
    SoftwareSQL,
    DatasetSQL,
    ComputationSQL,
    MetadataTypeEnumSQL
)
from fairscape_models.computation import Computation
import datetime

# Convert Pydantic Model to SQLAlchemy Class
entityKeys = [
    "guid",
    "name",
    "description",
]

ROCrateKeys = entityKeys + ["version"]
DatasetKeys = entityKeys + ["version", "fileFormat", "datePublished"]
SoftwareKeys = entityKeys + ["version"]
ComputationKeys = entityKeys + []

TypeMapping = {
    MetadataTypeEnumSQL.ROCRATE: ROCrateKeys,
    MetadataTypeEnumSQL.DATASET: DatasetKeys,
    MetadataTypeEnumSQL.SOFTWARE: SoftwareKeys,
    MetadataTypeEnumSQL.COMPUTATION: ComputationKeys
}


stripModel = lambda inputData, keyList: { key: inputData.__dict__[key] for key in keyList}

def setDatePublished(inputData):
    if not inputData.datePublished:
        inputData.datePublished = datetime.datetime.now().strftime("%m-%d-%Y")
    # TODO if computation dateCreated needs to exist
    return inputData

# convert elements into SQL Alchemy
ConvertElem = lambda inputElem, modelClass, modelKeys: modelClass(**stripModel(inputElem, modelKeys))

ConvertROCrateToSQL = lambda inputElem: ROCrateMetadataElemSQL(**stripModel(setDatePublished(inputElem), ROCrateKeys))
ConvertSoftwareToSQL = lambda inputElem: SoftwareSQL(**stripModel(setDatePublished(inputElem), SoftwareKeys))
ConvertDatasetToSQL = lambda inputElem: DatasetSQL(**stripModel(setDatePublished(inputElem), DatasetKeys))
ConvertComputationToSQL = lambda inputElem: ComputationSQL(**stripModel(setDatePublished(inputElem), ComputationKeys))