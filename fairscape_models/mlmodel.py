from pydantic import Field, ConfigDict, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, MLMODEL_TYPE
from fairscape_models.digital_object import DigitalObject

class MLModel(DigitalObject):
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Entity', "https://w3id.org/EVI#MLModel"], alias="@type")
    additionalType: Optional[str] = Field(default=MLMODEL_TYPE)
    dateModified: Optional[str] = Field(default=None)
    fileFormat: str = Field(alias="format")
    modelTask: Optional[str] = Field(default=None)
    modelArchitecture: Optional[str] = Field(default=None)
    trainedOn: Optional[List[IdentifierValue]] = Field(default=[])
    generatedBy: Optional[Union[IdentifierValue, List[IdentifierValue]]] = Field(default=[])
    derivedFrom: Optional[List[IdentifierValue]] = Field(default=[])

    @model_validator(mode='after')
    def populate_prov_fields(self):
        """Auto-populate PROV-O fields from EVI fields"""

        # Map generatedBy → prov:wasGeneratedBy
        if self.generatedBy:
            if isinstance(self.generatedBy, list):
                self.wasGeneratedBy = self.generatedBy
            else:
                self.wasGeneratedBy = [self.generatedBy]
        else:
            self.wasGeneratedBy = []

        # Map derivedFrom → prov:wasDerivedFrom
        self.wasDerivedFrom = self.derivedFrom or []

        # Map author → prov:wasAttributedTo
        if self.author:
            if isinstance(self.author, str):
                self.wasAttributedTo = [self.author]
            elif isinstance(self.author, list):
                self.wasAttributedTo = [a for a in self.author]
        else:
            self.wasAttributedTo = []

        return self
