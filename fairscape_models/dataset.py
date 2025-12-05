from pydantic import Field, ConfigDict, AliasChoices
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, DATASET_TYPE
from fairscape_models.digital_object import DigitalObject

class Dataset(DigitalObject):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Dataset", alias="@type")
    additionalType: Optional[str] = Field(default=DATASET_TYPE)
    datePublished: str = Field(...)
    keywords: List[str] = Field(...)
    fileFormat: str = Field(alias="format")
    dataSchema: Optional[IdentifierValue] = Field(
        validation_alias=AliasChoices('evi:Schema', 'EVI:Schema', 'schema', 'evi:schema'),
        serialization_alias='evi:Schema',
        default=None
    )
    generatedBy: Optional[Union[IdentifierValue, List[IdentifierValue]]] = Field(default=[])
    derivedFrom: Optional[List[IdentifierValue]] = Field(default=[])