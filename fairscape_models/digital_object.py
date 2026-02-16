from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models import __version__

class DigitalObject(BaseModel):
    """Base class for DigitalObject types (Dataset, Software, MLModel)"""
    guid: str = Field(alias="@id")
    name: str
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Entity', "https://w3id.org/EVI#DigitalObject"], alias="@type")
    author: Union[str, IdentifierValue, List[Union[str, IdentifierValue]]]
    description: str = Field(min_length=10)
    version: str = Field(default="0.1.0")
    associatedPublication: Optional[Union[str, List[str]]] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    contentUrl: Optional[Union[str, List[str]]] = Field(default=None)
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
    usedByComputation: Optional[List[IdentifierValue]] = Field(default=[])
    fairscapeVersion: str = __version__

    # PROV-O fields (auto-populated)
    wasGeneratedBy: Optional[List[Union[str, IdentifierValue]]] = Field(default=[], alias="prov:wasGeneratedBy")
    wasDerivedFrom: Optional[List[Union[str, IdentifierValue]]] = Field(default=[], alias="prov:wasDerivedFrom")
    wasAttributedTo: Optional[List[Union[str, IdentifierValue]]] = Field(default=[], alias="prov:wasAttributedTo")

    model_config = ConfigDict(extra="allow", populate_by_name=True)
