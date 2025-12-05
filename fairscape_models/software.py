from pydantic import Field, ConfigDict
from typing import Optional, List

from fairscape_models.fairscape_base import IdentifierValue, SOFTWARE_TYPE
from fairscape_models.digital_object import DigitalObject

class Software(DigitalObject):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Software", alias="@type")
    additionalType: Optional[str] = Field(default=SOFTWARE_TYPE)
    dateModified: Optional[str]
    fileFormat: str = Field(title="fileFormat", alias="format")
