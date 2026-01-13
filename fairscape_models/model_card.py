from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator

from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models.digital_object import DigitalObject


class ModelCard(DigitalObject):
    """Model Card for ML models as RO-Crate Dataset elements"""
    
    model_config = ConfigDict(extra="allow")
    
    guid: str = Field(alias="@id")
    
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Entity', "https://w3id.org/EVI#MLModel"], alias="@type")
    name: str
    description: str
    author: Union[str, List[str]]
    keywords: List[str]
    version: str
    
    modelType: Optional[Union[str, List[str]]] = Field(default=None)
    framework: Optional[Union[str, List[str]]] = Field(default=None)
    modelFormat: Optional[Union[str, List[str]]] = Field(default=None)
    trainingDataset: Optional[Union[str, List[IdentifierValue]]] = Field(default=None)
    generatedBy: Optional[IdentifierValue] = Field(default=None)
    derivedFrom: Optional[List[IdentifierValue]] = Field(default=[])
    
    parameters: Optional[float] = Field(default=None)
    inputSize: Optional[str] = Field(default=None)
    hasBias: Optional[str] = Field(default=None)
    intendedUseCase: Optional[str] = Field(default=None)
    usageInformation: Optional[str] = Field(default=None)
    
    baseModel: Optional[str] = Field(default=None)
    associatedPublication: Optional[Union[str, List[str]]] = Field(default=None)
    contentUrl: Union[str, List[str]] = Field(default=None)
    url: Optional[str] = Field(default=None)
    dataLicense: Optional[str] = Field(alias="license", default=None)
    citation: Optional[str] = Field(default=None)

    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])

    @model_validator(mode='after')
    def populate_prov_fields(self):
        """Auto-populate PROV-O fields from EVI fields"""

        # Map generatedBy → prov:wasGeneratedBy
        if self.generatedBy:
            self.wasGeneratedBy = [self.generatedBy]
        else:
            self.wasGeneratedBy = []

        if self.trainingDataset and self.derivedFrom == []:
            if isinstance(self.trainingDataset, list):
                self.derivedFrom = self.trainingDataset
            else:
                self.derivedFrom = [self.trainingDataset]

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