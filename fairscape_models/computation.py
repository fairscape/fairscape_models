from pydantic import BaseModel, Field
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, COMPUTATION_TYPE

class Computation(BaseModel):
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Computation")
    additionalType: Optional[str] = Field(default=COMPUTATION_TYPE)
    runBy: str
    description: str = Field(min_length=10)
    dateCreated: str
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    command: Optional[Union[List[str], str]] = Field(default=None)
    usedSoftware: Optional[List[IdentifierValue]] = Field(default=[])
    usedDataset: Optional[List[IdentifierValue]] = Field(default=[])
    generated: Optional[List[IdentifierValue]] = Field(default=[])