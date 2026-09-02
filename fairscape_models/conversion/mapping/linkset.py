"""RO-Crate to linkset (RFC 9264) conversion.

Builds the FAIR Signposting "Level 2" document for a crate: every file as an
`item` link, every identified author as an `author` link, plus `cite-as`,
`license`, `type` and `describedby`.

Unlike the Croissant and D4D mappings this is not a field-to-field rename, so it
is written as a function rather than a `ROCToTargetConverter` configuration —
the work is structural (one `hasPart` entry becomes one link) and reads better
as plain code.

Deployment URLs (`anchor`, `describedby`) are parameters: this package must not
know the address of any particular FAIRSCAPE deployment.
"""

import mimetypes
from typing import Any, Dict, List, Optional

from fairscape_models.conversion.mapping.croissant import map_format_to_mime_type
from fairscape_models.conversion.models.linkset import LinkContext, Linkset, LinkTarget
from fairscape_models.rocrate import ROCrateV1_2

# Short format names `map_format_to_mime_type` genuinely recognizes. Anything
# else falls through to text/plain there, which we must not repeat here: telling
# a client a JPEG is text/plain is worse than omitting the media type.
CROISSANT_KNOWN_FORMATS = frozenset(
    {
        "csv", ".csv",
        "json", ".json",
        "jsonl", ".jsonl", "jsonlines", ".jsonlines",
        "parquet", ".parquet",
        "txt", ".txt", "text", "plain",
        "tsv", ".tsv",
        "tar", ".tar",
        "zip", ".zip",
    }
)

# contentUrl sentinel used for entities that exist in the graph but whose bytes
# are not released. An `item` link to one would advertise access we don't grant.
EMBARGOED_SENTINEL = "embargoed"

SCHEMA_ORG_DATASET = "https://schema.org/Dataset"
SCHEMA_ORG_ABOUT_PAGE = "https://schema.org/AboutPage"

# Types whose contentUrl points at a file worth listing as an `item`.
CONTENT_TYPE_HINTS = ("Dataset", "Software", "MLModel", "Container", "DigitalObject")


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _is_http_uri(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _entity_field(entity: Any, *names: str) -> Any:
    """Read a field from a pydantic entity or a plain dict, trying each name.

    Entities in `@graph` are pydantic models whose python attribute names differ
    from their JSON-LD aliases (`fileFormat` vs `format`, `guid` vs `@id`), and
    `extra="allow"` means some values only exist in `model_extra`.
    """
    for name in names:
        if isinstance(entity, dict):
            if entity.get(name) is not None:
                return entity[name]
            continue
        value = getattr(entity, name, None)
        if value is not None:
            return value
        extra = getattr(entity, "model_extra", None) or {}
        if extra.get(name) is not None:
            return extra[name]
    return None


def _content_url(entity: Any) -> Optional[str]:
    """The first usable contentUrl, or None if absent or embargoed."""
    for candidate in _as_list(_entity_field(entity, "contentUrl")):
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        if candidate.strip().lower() == EMBARGOED_SENTINEL:
            continue
        if not _is_http_uri(candidate):
            # file:// paths and bare relative paths are not dereferenceable by
            # a remote client, so they are not signpostable.
            continue
        return candidate
    return None


def _media_type(file_format: Any, url: str) -> Optional[str]:
    """Resolve a media type, or None when we can't determine one confidently.

    Crates carry `format` as either a real media type ('image/jpeg'), a short
    name ('csv'), or an extension ('.parquet'). We never guess: an omitted
    `type` attribute is valid signposting, a wrong one misleads clients.
    """
    if isinstance(file_format, str) and file_format.strip():
        fmt = file_format.strip()
        if "/" in fmt:  # already a media type
            return fmt
        if fmt.lower() in CROISSANT_KNOWN_FORMATS or fmt.lower().startswith("git"):
            return map_format_to_mime_type(fmt)
        guessed, _ = mimetypes.guess_type(f"f.{fmt.lstrip('.').lower()}")
        if guessed:
            return guessed
    guessed, _ = mimetypes.guess_type(url)
    return guessed


def _person_uri(author: Any) -> Optional[str]:
    """A dereferenceable URI for an author, or None if only a name is known."""
    if _is_http_uri(author):
        return author
    if isinstance(author, str):
        return None
    identifier = _entity_field(author, "identifier")
    if _is_http_uri(identifier):
        return identifier
    guid = _entity_field(author, "guid", "@id")
    return guid if _is_http_uri(guid) else None


def _index_graph(crate: ROCrateV1_2) -> Dict[str, Any]:
    index = {}
    for entity in crate.metadataGraph:
        guid = _entity_field(entity, "guid", "@id")
        if isinstance(guid, str):
            index[guid] = entity
    return index


def _find_root(crate: ROCrateV1_2, index: Dict[str, Any]) -> Optional[Any]:
    """The crate's root data entity, via the metadata descriptor's `about`."""
    for entity in crate.metadataGraph:
        guid = _entity_field(entity, "guid", "@id")
        if guid == "ro-crate-metadata.json":
            about = _entity_field(entity, "about")
            about_id = _entity_field(_as_list(about)[0], "guid", "@id") if _as_list(about) else None
            if isinstance(about_id, str) and about_id in index:
                return index[about_id]
    # Fall back to the first entity typed as an RO-Crate root.
    for entity in crate.metadataGraph:
        types = " ".join(str(t) for t in _as_list(_entity_field(entity, "metadataType", "@type")))
        if "ROCrate" in types and _entity_field(entity, "hasPart") is not None:
            return entity
    return None


def _resolve_authors(root: Any, index: Dict[str, Any]) -> List[LinkTarget]:
    """Author links, deduped. Only authors carrying a URI can be signposted."""
    targets: List[LinkTarget] = []
    seen = set()
    candidates = _as_list(_entity_field(root, "author"))
    candidates += _as_list(_entity_field(root, "principalInvestigator"))

    for author in candidates:
        # A {"@id": ...} stub points at a Person elsewhere in the graph.
        guid = _entity_field(author, "guid", "@id") if not isinstance(author, str) else None
        resolved = index.get(guid, author) if isinstance(guid, str) else author

        uri = _person_uri(resolved)
        if not uri or uri in seen:
            continue
        seen.add(uri)
        name = _entity_field(resolved, "name")
        targets.append(LinkTarget(href=uri, title=name if isinstance(name, str) else None))
    return targets


def _resolve_items(root: Any, index: Dict[str, Any], max_items: Optional[int]) -> List[LinkTarget]:
    """One `item` link per part that has a dereferenceable contentUrl."""
    targets: List[LinkTarget] = []
    seen = set()

    for part in _as_list(_entity_field(root, "hasPart")):
        guid = _entity_field(part, "guid", "@id")
        entity = index.get(guid) if isinstance(guid, str) else None
        if entity is None:
            # Reference to an entity not present in this crate's graph (common
            # for release crates whose parts live in sub-crates).
            continue

        url = _content_url(entity)
        if not url or url in seen:
            continue
        seen.add(url)

        file_format = _entity_field(entity, "fileFormat", "format", "encodingFormat")
        targets.append(
            LinkTarget(
                href=url,
                type=_media_type(file_format, url),
                title=_entity_field(entity, "name"),
            )
        )
        if max_items is not None and len(targets) >= max_items:
            break
    return targets


def rocrate_to_linkset(
    crate: ROCrateV1_2,
    anchor: str,
    cite_as: Optional[str] = None,
    describedby_url: Optional[str] = None,
    describedby_type: str = "application/ld+json",
    max_items: Optional[int] = None,
    extra_linksets: Optional[List[str]] = None,
) -> Linkset:
    """Build the RFC 9264 linkset for ``crate``.

    Args:
        crate: the parsed RO-Crate.
        anchor: IRI of the landing page these links describe.
        cite_as: the resolvable HTTP form of the crate's persistent identifier.
            Crate ``@id`` values are frequently bare ARKs (``ark:59852/...``),
            which are not dereferenceable, so the caller — which knows the
            deployment's resolver address — should pass the HTTP form. Falls
            back to an http ``identifier`` or ``@id`` on the root entity.
        describedby_url: URL serving this crate's machine-readable metadata.
        describedby_type: media type of ``describedby_url``.
        max_items: cap on `item` links; ``None`` means no cap. Release crates can
            hold >100k parts, so callers serving those should page instead.
        extra_linksets: URLs of further linksets (e.g. one per sub-crate).

    Returns:
        A `Linkset` with a single anchored context. Relations with nothing to
        say are left unset and omitted on serialization.
    """
    index = _index_graph(crate)
    root = _find_root(crate, index)
    if root is None:
        return Linkset(linkset=[LinkContext(anchor=anchor)])

    context = LinkContext(anchor=anchor)

    # cite-as: the caller's resolvable PID if given, else an http identifier
    # (typically a DOI) or an http @id on the root.
    identifier = _entity_field(root, "identifier")
    root_guid = _entity_field(root, "guid", "@id")
    cite_as_uri = next((c for c in (cite_as, identifier, root_guid) if _is_http_uri(c)), None)
    if cite_as_uri:
        context.citeAs = [LinkTarget(href=cite_as_uri)]

    # type: what kind of thing this is, plus the landing-page marker the
    # signposting profile recommends.
    context.type = [LinkTarget(href=SCHEMA_ORG_DATASET), LinkTarget(href=SCHEMA_ORG_ABOUT_PAGE)]

    if describedby_url:
        conforms = _as_list(_entity_field(root, "conformsTo"))
        profile = _entity_field(conforms[0], "guid", "@id") if conforms else None
        context.describedby = [
            LinkTarget(
                href=describedby_url,
                type=describedby_type,
                profile=profile if _is_http_uri(profile) else None,
            )
        ]

    license_uri = _entity_field(root, "dataLicense", "license")
    if _is_http_uri(license_uri):
        context.license = [LinkTarget(href=license_uri)]

    authors = _resolve_authors(root, index)
    if authors:
        context.author = authors

    items = _resolve_items(root, index, max_items)
    if items:
        context.item = items

    if extra_linksets:
        context.linkset = [
            LinkTarget(href=url, type="application/linkset+json") for url in extra_linksets
        ]

    return Linkset(linkset=[context])
