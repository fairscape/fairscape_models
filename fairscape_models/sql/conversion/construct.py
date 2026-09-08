from fairscape_models.sql.models import (
    ROCrateMetadataElemSQL,
    SoftwareSQL,
    DatasetSQL,
    ComputationSQL,
    MetadataTypeEnumSQL
)
from fairscape_models.computation import Computation
from fairscape_models.fairscape_base import IdentifierValue
import datetime

# Convert Pydantic Model to SQLAlchemy Class
entityKeys = [
    "guid",
    "name",
    "description",
]

ROCrateKeys = entityKeys + ["version", "datePublished"]
DatasetKeys = entityKeys + ["version", "fileFormat", "datePublished"]
SoftwareKeys = entityKeys + ["version", "fileFormat", "datePublished"]
ComputationKeys = entityKeys + ["dateCreated"]

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
#ConvertComputationToSQL = lambda inputElem: ComputationSQL(**stripModel(setDatePublished(inputElem), ComputationKeys))

# computation
def ConvertComputationToSQL(inputElem: Computation) -> ComputationSQL:
    outputElem = ComputationSQL(**stripModel(setDatePublished(inputElem), ComputationKeys))

    # get single software guid for ComputationSQL.usedSoftware
    if inputElem.usedSoftware:
        if isinstance(inputElem.usedSoftware, list):
            # TODO deal with issue with list with multiple software specified in list
            usedSoftware=inputElem.usedSoftware[0]
            if isinstance(usedSoftware, IdentifierValue):
                outputElem.usedSoftware = usedSoftware.guid
            elif isinstance(usedSoftware, str):
                outputElem.usedSoftware = usedSoftware
        if isinstance(inputElem.usedSoftware, str):
            outputElem.usedSoftware = inputElem.usedSoftware
    return outputElem