from fairscape_models.sql.conversion.author import ConvertAuthorsSQL, TransformAuthors
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

standardKeys = [
    "keywords",
    "author", 
    "version",
]

ROCrateKeys = entityKeys + standardKeys + [ "datePublished"]
DatasetKeys = entityKeys + standardKeys + ["fileFormat", "datePublished"]
SoftwareKeys = entityKeys + ["author", "version"] + [ "fileFormat", "datePublished"]
ComputationKeys = entityKeys + ["dateCreated"]

TypeMapping = {
    MetadataTypeEnumSQL.ROCRATE: ROCrateKeys,
    MetadataTypeEnumSQL.DATASET: DatasetKeys,
    MetadataTypeEnumSQL.SOFTWARE: SoftwareKeys,
    MetadataTypeEnumSQL.COMPUTATION: ComputationKeys
}


stripModel = lambda inputData, keyList: { key: inputData.__dict__[key] for key in keyList}

def setAuthors(inputModel):
    inputModel.author = ConvertAuthorsSQL(inputModel)
    return inputModel

def setDatePublished(inputData):
    if not inputData.datePublished:
        inputData.datePublished = datetime.datetime.now().strftime("%m-%d-%Y")
    # TODO if computation dateCreated needs to exist
    return inputData

def process(inputModel):
    return setAuthors(setDatePublished(inputModel))

# convert elements into SQL Alchemy
ConvertElem = lambda inputElem, modelClass, modelKeys: modelClass(**stripModel(inputElem, modelKeys))

ConvertROCrateToSQL = lambda inputElem: ROCrateMetadataElemSQL(**stripModel(process(inputElem), ROCrateKeys))
ConvertSoftwareToSQL = lambda inputElem: SoftwareSQL(**stripModel(process(inputElem), SoftwareKeys))
ConvertDatasetToSQL = lambda inputElem: DatasetSQL(**stripModel(process(inputElem), DatasetKeys))
#ConvertComputationToSQL = lambda inputElem: ComputationSQL(**stripModel(setDatePublished(inputElem), ComputationKeys))

# computation
def ConvertComputationToSQL(inputElem: Computation) -> ComputationSQL:
    outputElem = ComputationSQL(**stripModel(setDatePublished(inputElem), ComputationKeys))
    outputElem.author = ConvertAuthorsSQL(inputElem)

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