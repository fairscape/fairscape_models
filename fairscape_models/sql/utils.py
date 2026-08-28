from fairscape_models.sql.models import MetadataTypeEnumSQL
from typing import List


def DetermineMetadataTypeSQL(inputType: str | List[str])-> MetadataTypeEnumSQL:
    """ Return the MetadataTypeEnumSQL corresponding to a model's MetadataType property
    """
    if isinstance(inputType, str):
        inputType = [inputType]

    # TODO rewrite
    if any(['ROCrate' in elem for elem in inputType]):
        return MetadataTypeEnumSQL.ROCRATE
    if any(['Dataset' in elem for elem in inputType]):
        return MetadataTypeEnumSQL.DATASET
    if any(['Software' in elem for elem in inputType]):
        return MetadataTypeEnumSQL.SOFTWARE
    if any(['Computation' in elem for elem in inputType]):
        return MetadataTypeEnumSQL.COMPUTATION
    if any(['Schema' in elem for elem in inputType]):
        return MetadataTypeEnumSQL.SCHEMA
    if any(['BioChemEntity' in elem for elem in inputType]):
        return MetadataTypeEnumSQL.BIO_CHEM_ENTITY