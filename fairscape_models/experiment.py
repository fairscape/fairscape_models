from pydantic import Field, ConfigDict, model_validator
from typing import Optional, List, Union
from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models.activity import Activity

class Experiment(Activity):
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Activity', "https://w3id.org/EVI#Experiment"], alias="@type")
    experimentType: str
    runBy: Union[str, IdentifierValue]
    datePerformed: str
    protocol: Optional[str] = Field(default=None)
    usedInstrument: Optional[List[IdentifierValue]] = Field(default=[])
    usedSample: Optional[List[IdentifierValue]] = Field(default=[])
    usedTreatment: Optional[List[IdentifierValue]] = Field(default=[])
    usedStain: Optional[List[IdentifierValue]] = Field(default=[])

    @model_validator(mode='after')
    def populate_prov_fields(self):
        """Auto-populate PROV-O fields from EVI fields"""
        # Aggregate all inputs into prov:used
        used_items = []
        if self.usedInstrument:
            used_items.extend(self.usedInstrument)
        if self.usedSample:
            used_items.extend(self.usedSample)
        if self.usedTreatment:
            used_items.extend(self.usedTreatment)
        if self.usedStain:
            used_items.extend(self.usedStain)
        self.used = used_items

        if self.runBy:
            self.wasAssociatedWith = [self.runBy]

        return self