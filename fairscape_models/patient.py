from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict
    )
from typing import (
  Optional,
  List,
  Union
)
from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models._version import __version__

class Patient(BaseModel):
  guid: str = Field(alias="@id")
  name: str
  metadataType: Optional[str] = Field(
    default="https://schema.org/Patient",
    alias="@type"
  )
  sdPublisher: str = Field(min_length=4)
  isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
  diagnosis: Optional[List[IdentifierValue]] = Field(default=[])
  drug: Optional[List[IdentifierValue]] = Field(default=[])
  healthCondition: Optional[List[IdentifierValue]] = Field(default=[])
  gender: Optional[str]
  birthDate: Optional[str] = Field(default=None)
  deathDate: Optional[str] = Field(default=None)
  fairscapeVersion: str = __version__
