from pydantic import Field, ConfigDict, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, ANNOTATION_TYPE
from fairscape_models.activity import Activity

class Annotation(Activity):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Annotation", alias="@type")
    additionalType: Optional[str] = Field(default=ANNOTATION_TYPE)
    createdBy: Union[str, IdentifierValue]
    dateCreated: str
    usedDataset: Optional[List[IdentifierValue]] = Field(default=[])

    @model_validator(mode='after')
    def populate_prov_fields(self):
        """Auto-populate PROV-O fields from EVI fields"""
        # Map usedDataset to prov:used (preserving their types)
        if self.usedDataset:
            self.used = self.usedDataset
        else:
            self.used = []

        # Map createdBy to prov:wasAssociatedWith (preserve type: str or IdentifierValue)
        if self.createdBy:
            self.wasAssociatedWith = [self.createdBy]

        return self
