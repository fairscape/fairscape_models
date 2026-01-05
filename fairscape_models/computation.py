from pydantic import Field, ConfigDict, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, COMPUTATION_TYPE
from fairscape_models.activity import Activity

class Computation(Activity):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Computation", alias="@type")
    additionalType: Optional[str] = Field(default=COMPUTATION_TYPE)
    runBy: Union[str, IdentifierValue]
    dateCreated: str
    additionalDocumentation: Optional[str] = Field(default=None)
    command: Optional[Union[List[str], str]] = Field(default=None)
    usedSoftware: Optional[List[IdentifierValue]] = Field(default=[])
    usedMLModel: Optional[List[IdentifierValue]] = Field(default=[])
    usedDataset: Optional[List[IdentifierValue]] = Field(default=[])

    @model_validator(mode='after')
    def populate_prov_fields(self):
        """Auto-populate PROV-O fields from EVI fields"""
        # Aggregate all inputs into prov:used
        used_items = []
        if self.usedSoftware:
            used_items.extend(self.usedSoftware)
        if self.usedMLModel:
            used_items.extend(self.usedMLModel)
        if self.usedDataset:
            used_items.extend(self.usedDataset)
        self.used = used_items

        if self.runBy:
            self.wasAssociatedWith = [self.runBy]

        return self
