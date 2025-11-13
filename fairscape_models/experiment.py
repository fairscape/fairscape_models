from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union
from fairscape_models.fairscape_base import IdentifierValue

class Experiment(BaseModel):
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Experiment", alias="@type")
    experimentType: str  
    runBy: str
    description: str = Field(min_length=10)
    datePerformed: str 
    associatedPublication: Optional[str] = Field(default=None)
    protocol: Optional[str] = Field(default=None) 
    usedInstrument: Optional[List[IdentifierValue]] = Field(default=[]) 
    usedSample: Optional[List[IdentifierValue]] = Field(default=[]) 
    usedTreatment: Optional[List[IdentifierValue]] = Field(default=[])
    usedStain: Optional[List[IdentifierValue]] = Field(default=[])
    generated: Optional[List[IdentifierValue]] = Field(default=[])
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
    model_config = ConfigDict(extra="allow")