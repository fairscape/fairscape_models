from pydantic import Field, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, CLAIM_TYPE
from fairscape_models.digital_object import DigitalObject


class Claim(DigitalObject):
    metadataType: Optional[Union[List[str], str]] = Field(
        default=['prov:Entity', "https://w3id.org/EVI#Claim"], alias="@type"
    )
    additionalType: Optional[str] = Field(default=CLAIM_TYPE)
    claimText: str = Field(alias="evi:state", description="Textual representation of the claim")
    supportedBy: Optional[List[IdentifierValue]] = Field(default=[])

    @model_validator(mode='after')
    def populate_prov_fields(self):
        self.metadataType = ['prov:Entity', "https://w3id.org/EVI#Claim"]
        if self.author:
            if isinstance(self.author, list):
                self.wasAttributedTo = self.author
            else:
                self.wasAttributedTo = [self.author]
        else:
            self.wasAttributedTo = []
        return self
