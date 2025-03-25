from pydantic import BaseModel, Field
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, SOFTWARE_TYPE

class Software(BaseModel): 
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Software")
    additionalType: Optional[str] = Field(default=SOFTWARE_TYPE)
    author: str = Field(min_length=4)
    dateModified: str
    version: str = Field(default="0.1.0")
    description: str =  Field(min_length=10)
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    fileFormat: str = Field(title="fileFormat", alias="format")
    usedByComputation: Optional[List[IdentifierValue]] = Field(default=[])
    contentUrl: Optional[str] = Field(default=None)

    model_config = ConfigDict(extra="allow")
