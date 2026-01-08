from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue

class Activity(BaseModel):
    """Base class for Activity types (Computation, Annotation, Experiment)"""
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Activity'], alias="@type")
    description: str = Field(min_length=10)
    associatedPublication: Optional[str] = Field(default=None)
    generated: Optional[List[IdentifierValue]] = Field(default=[])
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])

    # PROV-O fields (auto-populated)
    used: Optional[List[Union[str, IdentifierValue]]] = Field(default=[], alias="prov:used")
    wasAssociatedWith: Optional[List[Union[str, IdentifierValue]]] = Field(default=[], alias="prov:wasAssociatedWith")

    model_config = ConfigDict(extra="allow", populate_by_name=True)
