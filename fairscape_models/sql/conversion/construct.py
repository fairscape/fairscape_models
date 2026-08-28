from fairscape_models.sql.models import (
    ROCrateMetadataElemSQL,
    SoftwareSQL,
    DatasetSQL,
    ComputationSQL,
    MetadataTypeEnumSQL
)
import re

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

# convert elements into SQL Alchemy
ConvertElem = lambda inputElem, modelClass, modelKeys: modelClass(**stripModel(inputElem, modelKeys))

# TODO clean up the generation using ConvertElem
ConvertROCrateToSQL = lambda inputElem: ROCrateMetadataElemSQL(**stripModel(inputElem, ROCrateKeys))
ConvertSoftwareToSQL = lambda inputElem: SoftwareSQL(**stripModel(inputElem, SoftwareKeys))
ConvertDatasetToSQL = lambda inputElem: DatasetSQL(**stripModel(inputElem, DatasetKeys))
ConvertComputationToSQL = lambda inputElem: ComputationSQL(**stripModel(inputElem, ComputationKeys))
