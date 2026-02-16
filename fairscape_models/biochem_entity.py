from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, IdentifierPropertyValue
from fairscape_models._version import __version__

class BioChemEntity(BaseModel):
    """ Pydantic model for the Schema.org BioChemEntity datatype

    This class can apply to Protiens, Genes, Chemical Entities, or Biological Samples
    """
    guid: str = Field(alias="@id")
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Entity', 'evi:BioChemEntity'], alias="@type")
    name: str
    identifier: Optional[List[IdentifierPropertyValue]] = Field(default=[])
    associatedDisease: Optional[IdentifierValue] = Field(default=None)
    usedBy: Optional[List[IdentifierValue]] = Field(default=[])
    description: Optional[str] = Field(default=None)
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
    fairscapeVersion: str = __version__
    
    model_config = ConfigDict(extra="allow")