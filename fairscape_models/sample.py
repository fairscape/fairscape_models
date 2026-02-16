from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union, Dict
from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models._version import __version__

class Sample(BaseModel):
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Entity', "https://w3id.org/EVI#Sample"], alias="@type")
    author: Union[str, List[str]]
    description: str = Field(min_length=1)
    keywords: List[str] = Field(...)
    contentUrl: Optional[Union[str, List[str]]] = Field(default=None)
    cellLineReference: Optional[IdentifierValue] = Field(default=None) 
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
    fairscapeVersion: str = __version__

    model_config = ConfigDict(extra='allow')