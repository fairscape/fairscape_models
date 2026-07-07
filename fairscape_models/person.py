from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Union

from fairscape_models.fairscape_base import Identifier, IdentifierValue


class Organization(Identifier):
    """Schema.org Organization. `identifier` is the ROR URI when available."""
    guid: Optional[str] = Field(default=None, alias="@id")
    metadataType: str = Field(default="Organization", alias="@type")
    name: str
    identifier: Optional[str] = Field(
        default=None,
        description="Persistent identifier for the organization, typically a ROR URI (https://ror.org/...)."
    )
    url: Optional[str] = Field(default=None)
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Person(Identifier):
    """Schema.org Person. `identifier` is the ORCID URI when available."""
    guid: Optional[str] = Field(default=None, alias="@id")
    metadataType: str = Field(default="Person", alias="@type")
    name: str
    identifier: Optional[str] = Field(
        default=None,
        description="Persistent identifier for the person, typically an ORCID URI (https://orcid.org/...)."
    )
    email: Optional[str] = Field(default=None)
    affiliation: Optional[Union[str, IdentifierValue, Organization]] = Field(
        default=None,
        description="Affiliation as a plain string, a reference stub to an Organization in @graph, or an inline Organization.",
    )
    model_config = ConfigDict(extra="allow", populate_by_name=True)
