from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union
from fairscape_models.fairscape_base import IdentifierValue

class Instrument(BaseModel):
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Entity', "https://w3id.org/EVI#Instrument"], alias="@type")
    manufacturer: str = Field(min_length=4)  
    model: str
    description: str = Field(min_length=10)
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    usedByExperiment: Optional[List[IdentifierValue]] = Field(default=[])  # changed from usedByComputation
    contentUrl: Optional[str] = Field(default=None)
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
    model_config = ConfigDict(extra="allow")