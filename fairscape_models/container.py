from pydantic import Field, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, CONTAINER_TYPE
from fairscape_models.digital_object import DigitalObject


class Container(DigitalObject):
    metadataType: Optional[Union[List[str], str]] = Field(
        default=['prov:Entity', "https://w3id.org/EVI#Container"], alias="@type"
    )
    additionalType: Optional[str] = Field(default=CONTAINER_TYPE)
    packages: Optional[List[IdentifierValue]] = Field(default=[], alias="evi:packages")

    @model_validator(mode='after')
    def populate_prov_fields(self):
        self.metadataType = ['prov:Entity', "https://w3id.org/EVI#Container"]
        if self.author:
            if isinstance(self.author, list):
                self.wasAttributedTo = self.author
            else:
                self.wasAttributedTo = [self.author]
        else:
            self.wasAttributedTo = []
        return self
