"""Linkset models — RFC 9264 ``application/linkset+json``.

A linkset carries the typed links that describe a resource. FAIRSCAPE serves one
per RO-Crate so that a signposting client can enumerate a crate's files, authors
and license in a single request, without parsing RO-Crate JSON-LD.

This is "Level 2" of the FAIR Signposting Profile (https://signposting.org/):
the landing page advertises a compact set of links in HTTP ``Link`` headers plus
``rel="linkset"``, and the linkset document holds the exhaustive set.

Serialization (RFC 9264 section 4.2)::

    {
      "linkset": [
        {
          "anchor": "https://example.org/landing-page",
          "cite-as": [{"href": "https://example.org/ark:59852/abc"}],
          "item": [{"href": "https://example.org/data.csv", "type": "text/csv"}]
        }
      ]
    }
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

LINKSET_MEDIA_TYPE = "application/linkset+json"

# Relation types used by the FAIR Signposting Profile. Registered in the IANA
# link relation registry, except `linkset` which is registered by RFC 9264.
SIGNPOSTING_RELATIONS = (
    "author",
    "cite-as",
    "collection",
    "describedby",
    "item",
    "license",
    "linkset",
    "type",
)


class LinkTarget(BaseModel):
    """A single link target: an ``href`` plus optional target attributes."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    href: str = Field(description="Target IRI of the link.")
    type: Optional[str] = Field(
        default=None,
        description="Media type of the target, e.g. 'text/csv' or 'application/ld+json'.",
    )
    profile: Optional[str] = Field(
        default=None,
        description="Profile URI the target conforms to, e.g. the RO-Crate profile.",
    )
    title: Optional[str] = Field(default=None, description="Human-readable label for the target.")


class LinkContext(BaseModel):
    """Links anchored on one resource.

    Each field is a link relation type; the JSON keys are the relation names
    themselves, so `cite_as` serializes as ``cite-as``. Empty relations are
    dropped on serialization (``exclude_none``) rather than emitted as ``[]``.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    anchor: str = Field(description="IRI of the resource these links describe (the landing page).")

    citeAs: Optional[List[LinkTarget]] = Field(
        default=None,
        alias="cite-as",
        description="The persistent identifier to cite this resource by.",
    )
    author: Optional[List[LinkTarget]] = Field(
        default=None, description="Author identifiers, e.g. ORCID URIs."
    )
    license: Optional[List[LinkTarget]] = Field(
        default=None, description="License URI governing reuse."
    )
    type: Optional[List[LinkTarget]] = Field(
        default=None, description="Class URIs of the resource, e.g. https://schema.org/Dataset."
    )
    describedby: Optional[List[LinkTarget]] = Field(
        default=None, description="Machine-readable metadata describing the resource."
    )
    item: Optional[List[LinkTarget]] = Field(
        default=None, description="Content resources (files) belonging to this resource."
    )
    collection: Optional[List[LinkTarget]] = Field(
        default=None, description="The collection this resource belongs to; inverse of `item`."
    )
    linkset: Optional[List[LinkTarget]] = Field(
        default=None, description="Further linksets, used to page or nest large crates."
    )


class Linkset(BaseModel):
    """An ``application/linkset+json`` document."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    linkset: List[LinkContext] = Field(default_factory=list)

    def to_json(self) -> dict:
        """Serialize for an HTTP response: relation names as keys, no empty relations."""
        return self.model_dump(by_alias=True, exclude_none=True)
