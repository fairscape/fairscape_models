from pydantic import Field, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, ARTICLE_TYPE
from fairscape_models.digital_object import DigitalObject


class Article(DigitalObject):
    metadataType: Optional[Union[List[str], str]] = Field(
        default=['prov:Entity', "https://w3id.org/EVI#Article"], alias="@type"
    )
    additionalType: Optional[str] = Field(default=ARTICLE_TYPE)
    datePublished: Optional[str] = Field(default=None)
    keywords: Optional[List[str]] = Field(default=[])
    # DigitalObjects (Claims, Images, etc.) contained in this Article
    hasPart: Optional[List[IdentifierValue]] = Field(default=[])

    @model_validator(mode='after')
    def populate_prov_fields(self):
        self.metadataType = ['prov:Entity', "https://w3id.org/EVI#Article"]
        if self.author:
            if isinstance(self.author, list):
                self.wasAttributedTo = self.author
            else:
                self.wasAttributedTo = [self.author]
        else:
            self.wasAttributedTo = []
        return self
