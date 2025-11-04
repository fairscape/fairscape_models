from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union, Dict
from fairscape_models.fairscape_base import IdentifierValue

class Sample(BaseModel):
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Sample", alias="@type")
    author: Union[str, List[str]]
    description: str = Field(min_length=1)
    keywords: List[str] = Field(...)
    contentUrl: Optional[Union[str, List[str]]] = Field(default=None)
    cellLineReference: Optional[IdentifierValue] = Field(default=None) 

    model_config = ConfigDict(extra='allow')