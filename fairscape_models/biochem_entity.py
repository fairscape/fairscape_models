from pydantic import BaseModel, Field
from typing import Optional, List

from fairscape_models.fairscape_base import IdentifierValue, IdentifierPropertyValue

class BioChemEntity(BaseModel):
    """ Pydantic model for the Schema.org BioChemEntity datatype

    This class can apply to Protiens, Genes, Chemical Entities, or Biological Samples
    """
    guid: str = Field(alias="@id")
    metadataType: Optional[str] = Field(default="BioChemEntity", alias="@type")
    name: str
    identifier: Optional[List[IdentifierPropertyValue]] = Field(default=[])
    associatedDisease: Optional[IdentifierValue] = Field(default=None)
    usedBy: Optional[List[IdentifierValue]] = Field(default=[])
    description: Optional[str] = Field(default=None)