from pydantic import BaseModel, Field, ConfigDict, AliasChoices, field_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, DATASET_TYPE

class Dataset(BaseModel):
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Dataset")
    additionalType: Optional[str] = Field(default=DATASET_TYPE)
    author: Union[str, List[str]]
    datePublished: str = Field(...)
    version: str = Field(default="0.1.0")
    description: str = Field(min_length=10)
    keywords: List[str] = Field(...)
    associatedPublication: Optional[Union[str,List[str]]] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    fileFormat: str = Field(alias="format")
    dataSchema: Optional[IdentifierValue] = Field(
        validation_alias=AliasChoices('evi:Schema', 'EVI:Schema', 'schema','evi:schema'),
        serialization_alias='evi:Schema',
        default=None
    )
    generatedBy: Optional[Union[IdentifierValue, List[IdentifierValue]]] = Field(default=[])
    derivedFrom: Optional[List[IdentifierValue]] = Field(default=[])
    usedByComputation: Optional[List[IdentifierValue]] = Field(default=[])
    contentUrl: Optional[Union[str, List[str]]] = Field(default=None)

    model_config = ConfigDict(extra="allow")