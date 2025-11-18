from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

from fairscape_models.fairscape_base import IdentifierValue, ANNOTATION_TYPE

class Annotation(BaseModel):
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Annotation", alias="@type")
    additionalType: Optional[str] = Field(default=ANNOTATION_TYPE)
    createdBy: str
    description: str = Field(min_length=10)
    dateCreated: str
    associatedPublication: Optional[str] = Field(default=None)
    usedDataset: Optional[List[IdentifierValue]] = Field(default=[])
    generated: Optional[List[IdentifierValue]] = Field(default=[])
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])

    model_config = ConfigDict(extra="allow")
