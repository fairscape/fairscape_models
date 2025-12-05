from pydantic import Field, ConfigDict
from typing import Optional, List
from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models.activity import Activity

class Experiment(Activity):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Experiment", alias="@type")
    experimentType: str
    runBy: str
    datePerformed: str
    protocol: Optional[str] = Field(default=None)
    usedInstrument: Optional[List[IdentifierValue]] = Field(default=[])
    usedSample: Optional[List[IdentifierValue]] = Field(default=[])
    usedTreatment: Optional[List[IdentifierValue]] = Field(default=[])
    usedStain: Optional[List[IdentifierValue]] = Field(default=[])