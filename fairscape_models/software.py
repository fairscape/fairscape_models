from pydantic import Field, ConfigDict, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, SOFTWARE_TYPE
from fairscape_models.digital_object import DigitalObject

class Software(DigitalObject):
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Entity', "https://w3id.org/EVI#Software"], alias="@type")
    additionalType: Optional[str] = Field(default=SOFTWARE_TYPE)
    dateModified: Optional[str] = None
    fileFormat: str = Field(title="fileFormat", alias="format")

    @model_validator(mode='after')
    def populate_prov_fields(self):
        """Auto-populate PROV-O fields from EVI fields"""
        
        # Map author → prov:wasAttributedTo
        if self.author:
            if isinstance(self.author, list):
                self.wasAttributedTo = self.author
            else:
                self.wasAttributedTo = [self.author]
        else:
            self.wasAttributedTo = []

        return self
