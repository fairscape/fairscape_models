from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, SERVICE_TYPE
from fairscape_models._version import __version__


class Service(BaseModel):
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[Union[List[str], str]] = Field(
        default=['prov:SoftwareAgent', "https://w3id.org/EVI#Service"], alias="@type"
    )
    description: str = Field(min_length=10)
    serviceUrl: Optional[str] = Field(default=None)
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    usedByComputation: Optional[List[IdentifierValue]] = Field(default=[])
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
    fairscapeVersion: str = __version__

    model_config = ConfigDict(extra="allow", populate_by_name=True)
