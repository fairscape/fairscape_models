from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue

class DigitalObject(BaseModel):
    """Base class for DigitalObject types (Dataset, Software, MLModel)"""
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[str] = Field(default=None, alias="@type")
    author: Union[str, List[str]]
    description: str = Field(min_length=10)
    version: str = Field(default="0.1.0")
    associatedPublication: Optional[Union[str, List[str]]] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    contentUrl: Optional[Union[str, List[str]]] = Field(default=None)
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
    usedByComputation: Optional[List[IdentifierValue]] = Field(default=[])

    model_config = ConfigDict(extra="allow")
