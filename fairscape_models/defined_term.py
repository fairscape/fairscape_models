from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional, Union

from fairscape_models.fairscape_base import IdentifierValue


class DefinedTerm(BaseModel):
    """Schema.org DefinedTerm. `@id` is the ontology IRI when one exists
    (MeSH, EDAM, Cellosaurus, etc.); `identifier` is set to the same IRI when
    `@id` is an ARK fallback so the external identifier is still discoverable.
    """
    guid: Optional[str] = Field(default=None, alias="@id")
    metadataType: str = Field(default="DefinedTerm", alias="@type")
    name: str
    termCode: Optional[str] = Field(default=None)
    inDefinedTermSet: Optional[Union[str, IdentifierValue, Dict[str, Any]]] = Field(
        default=None,
        description="The ontology / scheme this term belongs to. Either a reference stub ({\"@id\": \"...\"}) or an inline scheme dict.",
    )
    identifier: Optional[str] = Field(
        default=None,
        description="External IRI for this term (e.g. MeSH / EDAM / Cellosaurus URI). Set when @id is an ARK fallback.",
    )
    model_config = ConfigDict(extra="allow", populate_by_name=True)
