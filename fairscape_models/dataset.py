from pydantic import Field, ConfigDict, AliasChoices, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, DATASET_TYPE
from fairscape_models.digital_object import DigitalObject

class Dataset(DigitalObject):
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Entity', "https://w3id.org/EVI#Dataset"], alias="@type")
    additionalType: Optional[str] = Field(default=DATASET_TYPE)
    datePublished: str = Field(...)
    keywords: List[str] = Field(...)
    fileFormat: str = Field(alias="format")
    dataSchema: Optional[IdentifierValue] = Field(
        validation_alias=AliasChoices('evi:Schema', 'EVI:Schema', 'schema', 'evi:schema'),
        serialization_alias='evi:Schema',
        default=None
    )
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

        # Map author
        if self.author:
            if isinstance(self.author, str):
                self.wasAttributedTo = [self.author]
            elif isinstance(self.author, list):
                self.wasAttributedTo = [a for a in self.author]
        else:
            self.wasAttributedTo = []

        return self