from pydantic import BaseModel, Field
from typing import Optional, List

from fairscape_models.fairscape_base import IdentifierValue, IdentifierPropertyValue
from fairscape_models._version import __version__

class MedicalCondition(BaseModel):
    """ Pydantic model for the Schema.org MedicalCondition datatype

    This class represents any condition of the human body that affects the normal functioning of a person, whether physically or mentally. Includes diseases, injuries, disabilities, disorders, syndromes, etc.
    """
    guid: str = Field(alias="@id")
    metadataType: Optional[str] = Field(default="MedicalCondition", alias="@type")
    name: str
    identifier: Optional[List[IdentifierPropertyValue]] = Field(default=[])
    drug: Optional[List[IdentifierValue]] = Field(default=[])
    usedBy: Optional[List[IdentifierValue]] = Field(default=[])
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
    description: str 
    fairscapeVersion: str = __version__