from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

from fairscape_models.fairscape_base import IdentifierValue

class Activity(BaseModel):
    """Base class for Activity types (Computation, Annotation, Experiment)"""
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[str] = Field(default=None, alias="@type")
    description: str = Field(min_length=10)
    associatedPublication: Optional[str] = Field(default=None)
    generated: Optional[List[IdentifierValue]] = Field(default=[])
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])

    model_config = ConfigDict(extra="allow")
