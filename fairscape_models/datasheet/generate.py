"""Build a `DatasheetPage` from an RO-Crate and render it to HTML.

`GenerateDatasheet.format` reads the crate once and fills the pydantic page
models in `fairscape_models.datasheet.models`; `GenerateDatasheet.generate`
hands the page to the Jinja template. Every value that reaches a template is
plain text, so crate-authored text is always autoescaped. The stylesheet is
the one exception: it is template-owned, not crate-authored, and is passed as
`Markup` so its selectors and quotes survive autoescaping.
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup
from pydantic import BaseModel

from fairscape_models.computation import Computation
from fairscape_models.dataset import Dataset, _human_size
from fairscape_models.experiment import Experiment
from fairscape_models.instrument import Instrument
from fairscape_models.defined_term import DefinedTerm
from fairscape_models.mlmodel import MLModel
from fairscape_models.person import Organization, Person
from fairscape_models.rocrate import (
    IRB,
    ROCrateMetadataElem,
    ROCrateMetadataFileElem,
    ROCrateV1_2,
)
from fairscape_models.sample import Sample
from fairscape_models.schema import Schema
from fairscape_models.software import Software
from fairscape_models.datasheet.models import (
    Badge,
    Card,
    CompositionSection,
    ContentRow,
    CrateMetadata,
    DatasheetPage,
    Details,
    Link,
    Links,
    NavEntry,
    Pattern,
    PatternInput,
    Patterns,
    Regulatory,
    Row,
    Stat,
    Summary,
    tally,
)

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(HERE, "templates")
DATASHEET_TEMPLATE_NAME = "datasheet.html.j2"
STYLE_NAME = "style.css"

#: Characters of the description shown in the summary lead before it is cut
#: back to a word boundary and linked to the full text.
LEAD_LENGTH = 500
#: Formats listed in the summary panel before "+N more".
SUMMARY_FORMATS = 8
#: Work patterns listed per card before "+N more patterns".
PATTERN_ROWS = 5
METADATA_FILE = "ro-crate-metadata.json"
NOTE_UNPUBLISHED = (
    "This sub-crate's own metadata is not published with the release (access "
    "to its data is controlled), so only the release's description of it is "
    "shown; its contents are not counted."
)

# Label, then the ROCrateMetadataElem attribute, for the AI Ready Details block.
USE_CASE_FIELDS: List[Tuple[str, str]] = [
    ("Intended Use Cases", "rai_data_use_cases"),
    ("Prohibited Uses", "prohibitedUses"),
    ("Limitations", "rai_data_limitations"),
    ("Potential Sources of Bias", "rai_data_biases"),
    ("Maintenance Plan", "rai_data_release_maintenance_plan"),
    ("Data Collection", "rai_data_collection"),
    ("Data Collection Type", "rai_data_collection_type"),
    ("Collection Timeframe", "rai_data_collection_timeframe"),
    ("Raw Data", "rai_data_collection_raw_data"),
    ("Missing Data", "rai_data_collection_missing_data"),
    ("Imputation Protocol", "rai_data_imputation_protocol"),
    ("Manipulation Protocol", "rai_data_manipulation_protocol"),
    ("Preprocessing Protocol", "rai_data_preprocessing_protocol"),
    ("Annotation Protocol", "rai_data_annotation_protocol"),
    ("Annotation Platform", "rai_data_annotation_platform"),
    ("Annotation Analysis", "rai_data_annotation_analysis"),
    ("Personal / Sensitive Information", "rai_personal_sensitive_information"),
    ("Social Impact", "rai_data_social_impact"),
    ("Content Warning", "contentWarning"),
    ("Subpopulations", "subpopulations"),
    ("Subsets", "subsets"),
    ("Sampling Strategies", "samplingStrategies"),
    ("Data Anomalies", "dataAnomalies"),
    ("Participant Privacy", "participantPrivacy"),
]

# Display name of each entity class in a card's contents table.
KINDS: List[Tuple[type, str]] = [
    (Dataset, "Dataset"),
    (Software, "Software"),
    (MLModel, "ML model"),
    (Computation, "Computation"),
    (Experiment, "Experiment"),
    (Schema, "Schema"),
    (Instrument, "Instrument"),
    (Sample, "Sample"),
]


@lru_cache(maxsize=1)
def _environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(default_for_string=True, default=True),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=False,
    )
    return env


@lru_cache(maxsize=1)
def _style_css() -> Markup:
    """The page stylesheet, template-owned and therefore safe to inline."""
    with open(os.path.join(TEMPLATE_DIR, STYLE_NAME), encoding="utf-8") as handle:
        return Markup(handle.read())


# -- text helpers -------------------------------------------------------------

def _href(value: Optional[str]) -> str:
    """`value` when it is an http(s) URL a page can link to, else ""."""
    value = (value or "").strip()
    return value if value.startswith(("http://", "https://")) else ""


def _mailto(value: str) -> str:
    """A mailto link for a bare email address; "" for prose such as
    "Name, email"."""
    value = (value or "").strip()
    if "@" in value and not any(c in value for c in " ,;"):
        return f"mailto:{value}"
    return ""


def _text(value: Any) -> str:
    """Display text for a string, a list, a reference or an inline node."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return ", ".join(t for t in (_text(v) for v in value) if t)
    if isinstance(value, dict):
        return _text(value.get("name")) or _text(value.get("@id"))
    if isinstance(value, BaseModel):
        name = getattr(value, "name", None) or (value.model_extra or {}).get("name")
        if name:
            return _text(name)
        return str(getattr(value, "guid", "") or "")
    return str(value)


def _names(value: Any) -> List[str]:
    """Names for an author-like field: a string, a node, or a list of them."""
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    return [t for t in (_text(v) for v in items) if t]


def _prose(value: Any) -> str:
    """Text for a `str | List[str]` field; "" when it holds node references
    rather than prose (the d4d fields accept both)."""
    if isinstance(value, list) and any(isinstance(v, (BaseModel, dict)) for v in value):
        return ""
    return _text(value)


def _yes_no(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _lead(description: str) -> Tuple[str, bool]:
    """The summary lead: the description, cut back to a word boundary when it
    runs past `LEAD_LENGTH`."""
    text = (description or "").strip()
    if len(text) <= LEAD_LENGTH:
        return text, False
    cut = text[:LEAD_LENGTH]
    if " " in cut:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(), True


def _search(name: str, keywords: List[str], formats: List[str]) -> str:
    """The lower-cased haystack a card and its index row share."""
    return f"{name} {' '.join(keywords)} {' '.join(formats)}".lower()


# -- reading a crate ----------------------------------------------------------

def _root(crate: ROCrateV1_2) -> ROCrateMetadataElem:
    """The crate's own metadata element: the one the descriptor is `about`.

    A release crate's graph also carries the metadata elements of its
    sub-crates, so the first `ROCrateMetadataElem` is not necessarily it."""
    about = next(
        (e.about.guid for e in crate.metadataGraph if isinstance(e, ROCrateMetadataFileElem)),
        None,
    )
    for elem in crate.metadataGraph:
        if isinstance(elem, ROCrateMetadataElem) and elem.guid == about:
            return elem
    return crate.getCrateMetadata()


def _crate_metadata(elem: ROCrateMetadataElem) -> CrateMetadata:
    """A crate root's descriptive fields, flattened to display text. The only
    place these fields are read from a root."""
    extra = elem.model_extra or {}
    conforms = elem.conformsTo if isinstance(elem.conformsTo, list) else [elem.conformsTo]
    license_ = elem.dataLicense or ""
    terms = elem.conditionsOfAccess or ""
    contact = elem.contactEmail or ""
    identifier = elem.identifier or ""
    access = _text(extra.get("contentUrl")) or elem.url or ""
    date_published = elem.datePublished or ""
    date_created = elem.dateCreated or ""
    date_modified = elem.dateModified or ""
    return CrateMetadata(
        id=elem.guid,
        id_href=_href(elem.guid),
        name=elem.name,
        description=elem.description or "",
        version=elem.version or "",
        date_published=date_published,
        date_created=date_created,
        date_modified=date_modified,
        size=elem.contentSize or "",
        authors=_names(elem.author),
        publisher=_text(elem.publisher),
        principal_investigator=_text(elem.principalInvestigator),
        contact=contact,
        contact_href=_mailto(contact),
        identifier_label="DOI" if not identifier or "doi" in identifier.lower() else "Identifier",
        identifier=identifier,
        identifier_href=_href(identifier),
        license=license_,
        license_href=_href(license_),
        terms_of_use=terms,
        terms_href=_href(terms),
        confidentiality=elem.confidentialityLevel or "",
        keywords=list(elem.keywords or []),
        citation=_names(elem.citation),
        publications=_names(elem.associatedPublication),
        funder=_text(elem.funder),
        copyright=elem.copyrightNotice or "",
        md5=_text(elem.md5) or _text(extra.get("MD5")),
        access_href=_href(access),
        data_governance=_text(elem.dataGovernanceCommittee),
        ethical_review=_text(elem.ethicalReview),
        completeness=_text(elem.completeness),
        based_on=_names(extra.get("isBasedOn")),
        conforms_to=[c.guid for c in conforms if c is not None],
        date=date_published or date_created or date_modified,
    )


def _subcrate_parts(
    root: ROCrateMetadataElem, crate: ROCrateV1_2
) -> List[Tuple[str, str, Optional[ROCrateMetadataElem]]]:
    """`(guid, name, element)` for each part of `root` that is itself a crate:
    typed as one in the `hasPart` stub, or described by its own metadata
    element in the graph. `element` is that description when present."""
    elems = {
        e.guid: e for e in crate.metadataGraph
        if isinstance(e, ROCrateMetadataElem) and e is not root
    }
    parts = []
    for part in root.hasPart or []:
        extra = part.model_extra or {}
        types = extra.get("@type") or []
        if isinstance(types, str):
            types = [types]
        is_crate = any("ROCrate" in str(t) for t in types) or part.guid in elems
        if not is_crate:
            continue
        elem = elems.get(part.guid)
        name = _text(extra.get("name")) or (elem.name if elem else part.guid)
        parts.append((part.guid, name, elem))
    return parts


#: Nodes that describe a crate rather than belong to its contents.
DESCRIPTIVE = (ROCrateMetadataElem, ROCrateMetadataFileElem, Person, Organization, DefinedTerm)


def _kind(entity: Any) -> Optional[str]:
    """The contents-table label for an entity; None for the crate's own
    elements, for descriptive nodes (people, organizations, terms) and for
    anything without a name."""
    if isinstance(entity, DESCRIPTIVE):
        return None
    for cls, label in KINDS:
        if isinstance(entity, cls):
            return label
    if getattr(entity, "name", None) and getattr(entity, "guid", None):
        return "Other"
    return None


def _access(entity: Any) -> Tuple[str, str]:
    """`(text, href)` for an entity's `contentUrl`: a URL links, prose such
    as "Embargoed" is shown as is."""
    url = _text(getattr(entity, "contentUrl", None))
    return url, _href(url)


def _access_label(entity: Any) -> str:
    text, href = _access(entity)
    if href:
        return "Available"
    return text or "Not specified"


def _patterns(computations: List[Computation], by_guid: Dict[str, Any]) -> Tuple[Patterns, Counter]:
    """`inputs -> outputs` in formats for each computation, grouped, plus a
    tally of input datasets that live outside the crate."""
    groups: Counter = Counter()
    external: Counter = Counter()
    for comp in computations:
        inputs: List[str] = []
        refs = (comp.usedDataset or []) + (comp.usedSoftware or []) + (comp.usedMLModel or [])
        for ref in refs:
            entity = by_guid.get(ref.guid)
            if entity is None:
                external[_text(ref)] += 1
                inputs.append("external")
            else:
                inputs.append(_text(getattr(entity, "fileFormat", None)) or "unknown")
        outputs = [
            _text(getattr(by_guid.get(ref.guid), "fileFormat", None)) or "unknown"
            for ref in (comp.generated or [])
        ]
        if inputs or outputs:
            groups[(tuple(sorted(set(inputs))), tuple(sorted(set(outputs))))] += 1
    rows = [
        Pattern(inputs=[PatternInput(formats=list(ins))] if ins else [], outputs=list(outs), n=n)
        for (ins, outs), n in groups.most_common()
    ]
    return Patterns(rows=rows[:PATTERN_ROWS], more=max(0, len(rows) - PATTERN_ROWS)), external


def _details(crate: ROCrateV1_2) -> Details:
    """Counts, formats, access and work patterns for a crate whose metadata is
    available."""
    graph = crate.metadataGraph
    datasets = crate.getDatasets()
    software = crate.getSoftware()
    models = crate.getMLModels()
    computations = crate.getComputations()
    experiments = crate.getExperiments()
    schemas = crate.getSchemas()
    instruments = [e for e in graph if isinstance(e, Instrument)]
    samples = [e for e in graph if isinstance(e, Sample)]
    other = sum(1 for e in graph if _kind(e) == "Other")
    by_guid = {e.guid: e for e in graph if getattr(e, "guid", None)}
    patterns, external = _patterns(computations, by_guid)
    return Details(
        files=len(datasets),
        models=len(models),
        software=len(software),
        instruments=len(instruments),
        samples=len(samples),
        experiments=len(experiments),
        computations=len(computations),
        schemas=len(schemas),
        other=other,
        with_provenance=sum(1 for d in datasets if d.wasGeneratedBy),
        file_formats=tally([d.fileFormat for d in datasets if d.fileFormat]),
        software_formats=tally([s.fileFormat for s in software if s.fileFormat]),
        model_formats=tally([m.fileFormat for m in models if m.fileFormat]),
        file_access=tally([_access_label(d) for d in datasets]),
        software_access=tally([_access_label(s) for s in software]),
        computation_patterns=patterns,
        experiment_types=tally([e.experimentType for e in experiments]),
        input_datasets=tally(list(external.elements())),
    )


def _contents(crate: ROCrateV1_2) -> List[ContentRow]:
    rows = []
    for entity in crate.metadataGraph:
        kind = _kind(entity)
        if kind is None:
            continue
        fmt = _text(getattr(entity, "fileFormat", None))
        access, access_href = _access(entity)
        rows.append(ContentRow(
            kind=kind,
            name=entity.name,
            id=entity.guid,
            id_href=_href(entity.guid),
            description=_text(getattr(entity, "description", None)),
            format=fmt,
            size=_text(getattr(entity, "contentSize", None)),
            access=access,
            access_href=access_href,
            search=f"{entity.name} {kind} {fmt}".lower(),
        ))
    return rows


# -- the page -----------------------------------------------------------------

class GenerateDatasheet:
    """Turn a crate (and, for a release, any of its sub-crates whose metadata
    is to hand) into the datasheet page.

    `generated_at` and `source` only feed the footer; pass `generated_at` to
    get reproducible output."""

    def __init__(
        self,
        inputCrate: ROCrateV1_2,
        subcrates: Optional[List[ROCrateV1_2]] = None,
        *,
        generated_at: Optional[str] = None,
        source: str = METADATA_FILE,
    ):
        self.rootCrate = inputCrate
        self.subcrates = subcrates or []
        self.generated_at = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M")
        self.source = source
        self.env = _environment()

    # -- composition --

    @staticmethod
    def _published_card(position: int, meta: CrateMetadata, crate: ROCrateV1_2) -> Card:
        details = _details(crate)
        return Card(
            position=position,
            anchor=f"subcrate-{position}",
            meta=meta,
            size=meta.size,
            metadata_path=METADATA_FILE,
            details=details,
            contents=_contents(crate),
            published=True,
            search=_search(meta.name, meta.keywords, [t.label for t in details.file_formats]),
        )

    @staticmethod
    def _unpublished_card(
        position: int, guid: str, name: str, elem: Optional[ROCrateMetadataElem]
    ) -> Card:
        if elem is not None:
            meta = _crate_metadata(elem)
            extra = elem.model_extra or {}
        else:
            meta = CrateMetadata(id=guid, id_href=_href(guid), name=name)
            extra = {}
        return Card(
            position=position,
            anchor=f"subcrate-{position}",
            meta=meta,
            size=meta.size,
            metadata_path=_text(extra.get("ro-crate-metadata")) or METADATA_FILE,
            published=False,
            notes=[NOTE_UNPUBLISHED],
            search=_search(meta.name, meta.keywords, []),
        )

    def _cards(
        self,
        meta: CrateMetadata,
        parts: List[Tuple[str, str, Optional[ROCrateMetadataElem]]],
    ) -> List[Card]:
        if not parts:
            return [self._published_card(1, meta, self.rootCrate)]
        supplied = {_root(sub).guid: sub for sub in self.subcrates}
        cards = []
        for position, (guid, name, elem) in enumerate(parts, 1):
            sub = supplied.get(guid)
            if sub is not None:
                cards.append(self._published_card(position, _crate_metadata(_root(sub)), sub))
            else:
                cards.append(self._unpublished_card(position, guid, name, elem))
        return cards

    # -- blocks --

    @staticmethod
    def _summary(root: ROCrateMetadataElem, meta: CrateMetadata, cards: List[Card],
                 subcrates: int) -> Summary:
        details = [c.details for c in cards if c.published]

        def count(rollup: Optional[int], attr: str) -> int:
            if rollup is not None:
                return rollup
            return sum(getattr(d, attr) for d in details)

        datasets = count(root.evi_dataset_count, "files")
        computations = count(root.evi_computation_count, "activities")
        software = count(root.evi_software_count, "software")
        size = meta.size
        if not size and root.evi_total_content_size_bytes:
            size = _human_size(root.evi_total_content_size_bytes)
        formats = list(root.evi_formats or [])
        if not formats:
            seen: Dict[str, None] = {}
            for d in details:
                for t in d.file_formats:
                    seen.setdefault(t.label, None)
            formats = list(seen)
        description, truncated = _lead(meta.description)
        return Summary(
            description=description,
            truncated=truncated,
            stats=[
                Stat(label="Total size", n=size or "—"),
                Stat(label="Datasets", n=str(datasets)),
                Stat(label="Computations", n=str(computations)),
                Stat(label="Software", n=str(software)),
            ],
            extra=[Stat(label="sub-crates", n=str(subcrates))] if subcrates else [],
            entities=datasets + computations + software,
            formats=formats[:SUMMARY_FORMATS],
            formats_more=max(0, len(formats) - SUMMARY_FORMATS),
            access_href=meta.access_href,
        )

    @staticmethod
    def _overview(meta: CrateMetadata) -> List[Row]:
        rows = [
            Row.of("RO-Crate ID", meta.id, id="accession", href=meta.id_href, kind="mono"),
            Row.of(meta.identifier_label, meta.identifier, id="doi", href=meta.identifier_href,
                   missing="Not specified"),
            Row.of("Release Date", meta.date_published, id="release-date"),
            Row.of("Version", meta.version, id="version", kind="mono"),
            Row.of("Description", meta.description, id="description"),
            Row.of("Authors", ", ".join(meta.authors), id="authors"),
            Row.of("Publisher", meta.publisher, id="publisher"),
            Row.of("Principal Investigator", meta.principal_investigator, id="principal-investigator"),
            Row.of("Contact Email", meta.contact, id="contact-email", href=meta.contact_href),
            Row.of("Data Governance Committee", meta.data_governance, id="data-governance"),
            Row.of("Ethical Review", meta.ethical_review, id="ethical-review"),
            Row.of("Copyright", meta.copyright, id="copyright"),
            Row.of("License", meta.license, id="license", href=meta.license_href),
            Row.of("Terms of Use", meta.terms_of_use, id="terms-of-use", href=meta.terms_href),
            Row.of("HL7 Confidentiality Level", meta.confidentiality, id="confidentiality-level"),
            Row.of("Keywords", ", ".join(meta.keywords), id="keywords"),
            Row.of("Cite As", ", ".join(meta.citation), id="citation"),
            Row.of("Related Publications", id="publications", kind="list",
                   items=[Link(text=p, href=_href(p)) for p in meta.publications]),
            Row.of("Funding", meta.funder, id="funding"),
            Row.of("Completeness", meta.completeness, id="completeness"),
            Row.of("Based On", id="based-on", kind="list",
                   items=[Link(text=b, href=_href(b)) for b in meta.based_on]),
            Row.of("Conforms To", id="conforms-to", kind="list",
                   items=[Link(text=c, href=_href(c)) for c in meta.conforms_to]),
        ]
        return [r for r in rows if r]

    @staticmethod
    def _regulatory(root: ROCrateMetadataElem) -> Regulatory:
        irb: Any = root.irb or ""
        if isinstance(irb, IRB):
            irb = irb.model_dump(by_alias=True, exclude_none=True)
        return Regulatory(
            human_subject_research=_text(root.humanSubjectResearch),
            deidentified=_yes_no(root.deidentified),
            fda_regulated=_yes_no(root.fdaRegulated),
            irb_protocol_id=root.irbProtocolId or "",
            irb=irb,
            exemptions=root.humanSubjectExemption or "",
            informed_consent=_prose(root.informedConsent),
            at_risk_populations=_prose(root.atRiskPopulations),
        )

    @staticmethod
    def _use_cases(root: ROCrateMetadataElem) -> List[Row]:
        rows = [Row.of(label, _prose(getattr(root, attr))) for label, attr in USE_CASE_FIELDS]
        return [r for r in rows if r]

    @staticmethod
    def _distribution(meta: CrateMetadata) -> List[Row]:
        rows = [
            Row.of("Publisher", meta.publisher),
            Row.of("License", meta.license, href=meta.license_href),
            Row.of("Release Date", meta.date_published),
            Row.of("Version", meta.version, kind="mono"),
            Row.of("Access", meta.access_href, href=meta.access_href),
            Row.of(meta.identifier_label, meta.identifier, href=meta.identifier_href),
            Row.of("Content Size", meta.size, kind="mono"),
        ]
        return [r for r in rows if r]

    @staticmethod
    def _badges(meta: CrateMetadata) -> List[Badge]:
        badges = []
        if meta.version:
            badges.append(Badge(label=f"Version {meta.version}"))
        if meta.license:
            badges.append(Badge(label="License", href=meta.license_href, title=meta.license))
        if meta.date_published:
            badges.append(Badge(label=f"Released {meta.date_published}"))
        return badges

    @staticmethod
    def _nav(cards: List[Card], use_cases: List[Row], distribution: List[Row]) -> List[NavEntry]:
        nav = [
            NavEntry(href="#datasheet-summary", label="Datasheet Summary"),
            NavEntry(href="#dataset-details", label="Release Overview"),
        ]
        if use_cases:
            nav.append(NavEntry(href="#ai-readiness", label="AI Ready Details"))
        children: List[NavEntry] = []
        if len(cards) > 1:
            children = [NavEntry(href="#composition", label="All datasets")]
            children += [NavEntry(href=f"#{c.anchor}", label=c.meta.name) for c in cards]
        nav.append(NavEntry(href="#composition", label="Composition", children=children))
        if distribution:
            nav.append(NavEntry(href="#distribution", label="Distribution"))
        return nav

    # -- entry points --

    def format(self) -> DatasheetPage:
        """Use the rocrate metadata to generate the DatasheetPage object."""
        root = _root(self.rootCrate)
        meta = _crate_metadata(root)
        parts = _subcrate_parts(root, self.rootCrate)
        cards = self._cards(meta, parts)
        use_cases = self._use_cases(root)
        distribution = self._distribution(meta)
        return DatasheetPage(
            kicker="Datasheet",
            title=meta.name,
            ark=meta.id,
            ark_href=meta.id_href,
            chips=meta.keywords,
            badges=self._badges(meta),
            body_class="has-nav",
            source=self.source,
            generated_at=self.generated_at,
            nav=self._nav(cards, use_cases, distribution),
            summary=self._summary(root, meta, cards, len(parts)),
            overview=self._overview(meta),
            regulatory=self._regulatory(root),
            use_cases=use_cases,
            composition=CompositionSection(cards=cards, is_release=bool(parts)),
            distribution=distribution,
            links=Links(),
        )

    def generate(self, outputPath: Optional[str] = None) -> str:
        """Render the datasheet HTML, writing it to `outputPath` when given."""
        page = self.format()
        template = self.env.get_template(DATASHEET_TEMPLATE_NAME)
        context = page.model_dump()
        context["style_css"] = _style_css()
        html = template.render(**context)
        if outputPath:
            with open(outputPath, "w", encoding="utf-8", newline="") as handle:
                handle.write(html)
        return html
