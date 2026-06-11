"""Graph-only evidence extraction for the v2 AI-Ready grader.

Ported from the ``fairscape-grader`` deterministic extractor
(``rubrics/ai-ready/extract.py``), stripped of all filesystem access so
it can run on an already-merged metadata graph — the same input the
server's MongoDB path and the CLI both have in memory.

The public surface is :func:`build_evidence`, which walks the merged
graph once and returns an :class:`Evidence` snapshot. The v2 scorers in
``AIReadyV2.py`` consume that snapshot; they never touch the graph
directly. Detector classes and field-alias bundles are kept as close to
the grader's originals as possible so the two stay comparable.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional, Tuple

EVI_PREFIX = "https://w3id.org/EVI#"


# ---------------------------------------------------------------------------
# Type and field helpers
# ---------------------------------------------------------------------------

def type_tokens(entity: dict) -> List[str]:
    """Flat list of type strings (@type / metadataType / additionalType)."""
    tokens: List[str] = []
    for key in ("@type", "metadataType", "additionalType"):
        v = entity.get(key)
        if isinstance(v, list):
            tokens.extend(str(x) for x in v)
        elif v:
            tokens.append(str(v))
    return tokens


def has_type(entity: dict, name: str) -> bool:
    return any(name in t for t in type_tokens(entity))


def is_dataset(entity: dict) -> bool:
    # ROCrates are also typed as Dataset; exclude them from Dataset counts.
    return has_type(entity, "Dataset") and not has_type(entity, "ROCrate")


def is_software(entity: dict) -> bool:
    return has_type(entity, "Software")


def is_schema(entity: dict) -> bool:
    return has_type(entity, "Schema")


def is_computation(entity: dict) -> bool:
    return has_type(entity, "Computation")


def is_experiment(entity: dict) -> bool:
    return has_type(entity, "Experiment")


def is_sample(entity: dict) -> bool:
    return has_type(entity, "Sample")


def is_instrument(entity: dict) -> bool:
    return has_type(entity, "Instrument")


def is_rocrate(entity: dict) -> bool:
    return has_type(entity, "ROCrate")


def first_present(entity: dict, *keys: str) -> Any:
    """First non-empty value among the given keys, or None."""
    for k in keys:
        v = entity.get(k)
        if v not in (None, "", [], {}):
            return v
    return None


def as_list(v: Any) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


# Field-alias bundles drawn from fairscape_models. Canonical key first,
# then known synonyms / namespaced variants.
HASH_KEYS = ("md5", "MD5", "sha256", "SHA256", "hash", "contentChecksum")
USED_SOFTWARE_KEYS = ("usedSoftware", "evi:usedSoftware", f"{EVI_PREFIX}usedSoftware")
USED_DATASET_KEYS = ("usedDataset", "evi:usedDataset", f"{EVI_PREFIX}usedDataset")
INPUTS_KEYS = USED_DATASET_KEYS + (f"{EVI_PREFIX}inputs", "evi:inputs", "used", "prov:used")
OUTPUTS_KEYS = ("generated", "prov:generated", f"{EVI_PREFIX}outputs", "evi:outputs")
FORMAT_KEYS = ("format", "fileFormat", "encodingFormat")
SCHEMA_LINK_FALLBACK_KEYS = ("conformsTo", "dataSchema")
CONTENT_URL_KEYS = ("contentUrl", "url", "distribution")

PROV_LINK_FIELDS = (
    "wasGeneratedBy", "prov:wasGeneratedBy", "wasDerivedFrom", "prov:wasDerivedFrom",
    "derivedFrom", "generatedBy", "isPartOf", "usedByComputation",
    "evi:usedSoftware", f"{EVI_PREFIX}usedSoftware", "evi:usedSample", f"{EVI_PREFIX}usedSample",
    "evi:usedInstrument", f"{EVI_PREFIX}usedInstrument",
    "usedSoftware", "usedSample", "usedInstrument", "usedDataset",
    "used", "prov:used", "generated", "prov:generated",
)


def has_hash(entity: dict) -> bool:
    return any(first_present(entity, k) is not None for k in HASH_KEYS)


def get_used_software(entity: dict) -> Any:
    return first_present(entity, *USED_SOFTWARE_KEYS)


def get_inputs(entity: dict) -> Any:
    return first_present(entity, *INPUTS_KEYS)


def get_outputs(entity: dict) -> Any:
    return first_present(entity, *OUTPUTS_KEYS)


def get_format(entity: dict) -> Any:
    return first_present(entity, *FORMAT_KEYS)


def _local_name(key: str) -> str:
    for sep in ("#", ":"):
        if sep in key:
            key = key.rsplit(sep, 1)[-1]
    return key


def get_dataset_schema_link(entity: dict) -> Any:
    # Any key whose local name is "schema" (covers every prefix/case combo of
    # evi:Schema) plus conformsTo / dataSchema fallbacks.
    for k, v in entity.items():
        if v in (None, "", [], {}):
            continue
        if _local_name(k).lower() == "schema":
            return v
    return first_present(entity, *SCHEMA_LINK_FALLBACK_KEYS)


def has_provenance_link(entity: dict) -> bool:
    return any(first_present(entity, k) is not None for k in PROV_LINK_FIELDS)


def is_embargoed(entity: dict) -> bool:
    url = first_present(entity, *CONTENT_URL_KEYS)
    if isinstance(url, str) and "embargo" in url.lower():
        return True
    am = entity.get("accessMode")
    if isinstance(am, str) and "embargo" in am.lower():
        return True
    return False


def get_additional_property(entity: dict, name: str) -> Optional[str]:
    for prop in (entity.get("additionalProperty") or []):
        if isinstance(prop, dict) and (prop.get("name") or "").lower() == name.lower():
            return prop.get("value")
    return None


DATASET_SOURCE_KEYS = (
    "wasDerivedFrom", "prov:wasDerivedFrom", "derivedFrom", "isBasedOn",
    "generatedBy", "wasGeneratedBy", "prov:wasGeneratedBy",
)


def has_dataset_source(entity: dict) -> bool:
    """A Dataset is 'sourced' (rubric 1.a) if it declares where it came
    from: a derivedFrom/wasDerivedFrom edge, a generatedBy/wasGeneratedBy
    edge (a Computation that produced it is just as resolvable an origin as
    a source dataset), or a recognizable specialist-repo accession on its
    contentUrl."""
    if first_present(entity, *DATASET_SOURCE_KEYS):
        return True
    return bool(AccessionDetector.detect(first_present(entity, *CONTENT_URL_KEYS)))


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------

class StandardsDetector:
    """Map @context namespaces to recognized standards / vocabularies."""

    MARKERS: ClassVar[Tuple[Tuple[str, str], ...]] = (
        ("schema.org", "schema.org"), ("w3id.org/evi", "EVI"), ("evi", "EVI"),
        ("dcat", "DCAT"), ("croissant", "Croissant"), ("ml-commons.org", "Croissant"),
        ("frictionlessdata", "Frictionless"), ("json-schema.org", "JSON Schema"),
        ("rai", "RAI"), ("d4d", "D4D"), ("prov", "PROV-O"), ("datacite", "DataCite"),
    )

    @classmethod
    def detect(cls, context_namespaces: List[str]) -> List[str]:
        blob = " ".join(str(x) for x in context_namespaces).lower()
        found: List[str] = []
        for marker, label in cls.MARKERS:
            if marker in blob and label not in found:
                found.append(label)
        return found


class ArchiveDetector:
    """Recognize FAIR-compliant archive hostnames + persistent-ID patterns."""

    HOSTNAMES: ClassVar[Dict[str, str]] = {
        "dataverse": "Dataverse", "zenodo.org": "Zenodo", "physionet.org": "PhysioNet",
        "fairhub": "FAIRhub", "biostudies": "BioStudies", "dbgap": "dbGaP",
        "ncbi.nlm.nih.gov": "NCBI", "ebi.ac.uk": "EBI", "ncbi.nlm.nih.gov/geo": "GEO",
        "massive.ucsd.edu": "MassIVE", "proteinatlas": "Human Protein Atlas",
        "softwareheritage.org": "Software Heritage", "figshare.com": "Figshare",
        "osf.io": "OSF", "dryad": "Dryad", "github.com": "GitHub",
    }
    SUSTAINABLE: ClassVar[Tuple[str, ...]] = (
        "zenodo", "softwareheritage", "figshare", "osf.io", "dryad", "doi.org",
    )

    @classmethod
    def detect(cls, *texts: Optional[Any]) -> List[str]:
        found: List[str] = []
        for t in texts:
            if not t:
                continue
            s = json.dumps(t, default=str).lower() if not isinstance(t, str) else t.lower()
            for marker, label in cls.HOSTNAMES.items():
                if marker in s and label not in found:
                    found.append(label)
        return found

    @classmethod
    def is_persistent_id(cls, value: Optional[Any]) -> bool:
        if not value:
            return False
        s = str(value).lower()
        return any(h in s for h in ("doi.org", "hdl.handle.net", "n2t.net", "ark:", "/ark/", "purl.org"))

    @classmethod
    def is_sustainable_archive(cls, value: Optional[Any]) -> bool:
        s = str(value or "").lower()
        return any(host in s for host in cls.SUSTAINABLE)


class AccessionDetector:
    """Pattern-match specialist-repo accession prefixes in contentUrl strings."""

    PATTERNS: ClassVar[Dict[str, Tuple[str, ...]]] = {
        "GEO": ("GSE", "GDS"), "SRA": ("SRR", "SRX", "SRP", "PRJ"), "PRIDE": ("PXD",),
        "MassIVE": ("MSV",), "BioStudies": ("S-BSST",), "dbGaP": ("phs",),
        "EGA": ("EGAS", "EGAD"), "ENA": ("ERR", "ERX", "ERP"), "ArrayExpress": ("E-MTAB", "E-GEOD"),
    }

    @classmethod
    def detect(cls, contentUrl: Any) -> List[Tuple[str, str]]:
        if not contentUrl:
            return []
        urls = contentUrl if isinstance(contentUrl, list) else [contentUrl]
        found: List[Tuple[str, str]] = []
        for u in urls:
            if not isinstance(u, str):
                continue
            for repo, prefixes in cls.PATTERNS.items():
                if any(p in u for p in prefixes):
                    found.append((repo, u[:120]))
                    break
        return found


class OntologyDetector:
    """Count entities carrying ontology IRIs."""

    MARKERS: ClassVar[Tuple[str, ...]] = (
        "meshb.nlm.nih.gov", "nlm.nih.gov/mesh", "purl.obolibrary.org",
        "edamontology.org", "ncithesaurus", "ncit", "geneontology.org",
    )

    @classmethod
    def count(cls, entities: List[dict]) -> int:
        n = 0
        for e in entities:
            blob = json.dumps(e, default=str).lower()
            if any(m in blob for m in cls.MARKERS):
                n += 1
        return n


class SchemaStandardDetector:
    """Detect standard-conformance signals in Schema entities."""

    JSON_SCHEMA_RE: ClassVar[re.Pattern] = re.compile(
        r"json-schema\.org/draft/?[0-9\-]*/?schema", re.IGNORECASE
    )
    STANDARD_STRINGS: ClassVar[Tuple[str, ...]] = (
        "schema.org", "w3id.org/evi", "frictionless", "json-schema", "loinc",
        "omop", "ga4gh", "fhir", "datacite", "dcat",
    )

    @classmethod
    def schema_references_standard(cls, schema_entity: dict) -> bool:
        blob = json.dumps(schema_entity, default=str)
        lower = blob.lower()
        if cls.JSON_SCHEMA_RE.search(blob):
            return True
        if any(s in lower for s in cls.STANDARD_STRINGS):
            return True
        if "conformsto" in lower or "schemaversion" in lower:
            return True
        return False


# ---------------------------------------------------------------------------
# Format buckets
# ---------------------------------------------------------------------------

PUBLISHED_FORMATS = {
    "csv", "tsv", "parquet", "hdf5", "h5", "h5ad", "fits", "nifti", "bam", "sam",
    "fastq", "fastq.gz", "json", "jsonl", "ndjson", "zarr", "image/jpeg",
    "image/png", "image/tiff", "tiff", "tif", "wav", "mp3", "flac", "txt",
    "xml", "html", "pdf", "yaml", "yml", "rdf", "ttl", "owl",
}
PROPRIETARY_FORMATS = {".d", ".d directory group", "raw", ".raw"}
SOFTWARE_RUNTIME_FORMATS = {"unknown", "executable"}
TABULAR_FORMATS = {
    "csv", "tsv", "parquet", "h5ad", "jsonl", "ndjson",
    "arrow", "feather", "xlsx", "xls", "ods", "orc", "avro",
}
CONTAINER_MARKERS = ("docker", "singularity", "apptainer", "container", "ghcr.io", "quay.io")
ENV_REQUIREMENT_KEYS = (
    "softwareRequirements", "runtimePlatform", "processorRequirements",
    "memoryRequirements", "storageRequirements", "operatingSystem",
    "containerImage", "requirements",
)


def is_tabular_dataset(entity: dict) -> bool:
    fmt = get_format(entity)
    if not fmt:
        return False
    candidates = fmt if isinstance(fmt, list) else [fmt]
    for f in candidates:
        if str(f).strip().lower().lstrip(".") in TABULAR_FORMATS:
            return True
    return False


def _format_buckets(format_distribution: Counter) -> Tuple[int, int]:
    """Return (published_count, proprietary_count) over the format histogram,
    ignoring software-runtime placeholders."""
    published = 0
    proprietary = 0
    for fmt, count in format_distribution.items():
        key = str(fmt).strip().lower()
        if key in SOFTWARE_RUNTIME_FORMATS:
            continue
        if key in PUBLISHED_FORMATS or key.lstrip(".") in PUBLISHED_FORMATS:
            published += count
        elif key in PROPRIETARY_FORMATS:
            proprietary += count
    return published, proprietary


# ---------------------------------------------------------------------------
# Root-level helpers
# ---------------------------------------------------------------------------

HL7_CONFIDENTIALITY_CODES = {"unrestricted", "normal", "restricted", "very restricted", "u", "n", "r", "v"}


def confidentiality_is_hl7(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().lower() in HL7_CONFIDENTIALITY_CODES


def is_resolvable_license(value: Optional[Any]) -> bool:
    if not value:
        return False
    s = str(value).lower()
    if s.startswith("http"):
        return True
    spdx_prefixes = ("cc-", "cc0", "mit", "apache", "gpl", "bsd", "mpl", "lgpl", "0bsd")
    return any(s.startswith(p) for p in spdx_prefixes)


def author_orcid_coverage(author_value: Any) -> Tuple[int, int]:
    """Return (author_count, authors_with_orcid_count). Handles
    semicolon-separated strings and list-of-Person dicts."""
    if isinstance(author_value, str):
        names = [a.strip() for a in author_value.split(";") if a.strip()]
        with_orcid = sum(1 for n in names if "orcid.org" in n.lower())
        return len(names), with_orcid
    if isinstance(author_value, list):
        author_count = len(author_value)
        with_orcid = 0
        for a in author_value:
            if isinstance(a, dict):
                blob = (str(a.get("@id", "")) + " " + str(a.get("identifier", ""))).lower()
                if "orcid.org" in blob:
                    with_orcid += 1
            elif isinstance(a, str) and "orcid.org" in a.lower():
                with_orcid += 1
        return author_count, with_orcid
    if isinstance(author_value, dict):
        blob = (str(author_value.get("@id", "")) + " " + str(author_value.get("identifier", ""))).lower()
        return 1, (1 if "orcid.org" in blob else 0)
    return 0, 0


def publisher_has_ror(publisher: Any) -> bool:
    s = json.dumps(publisher, default=str).lower() if isinstance(publisher, dict) else str(publisher or "").lower()
    return "ror.org" in s


def scan_irb_refs(root: dict) -> bool:
    for key in ("irb", "irbProtocolId", "ethicalReview", "humanSubjectExemption"):
        if root.get(key):
            return True
    blob = json.dumps(root, default=str)
    return bool(re.search(r"\bIRB\b|\bprotocol\b", blob, re.IGNORECASE))


def find_datasheet_entity(entities: List[dict]) -> bool:
    for e in entities:
        blob = " ".join(str(e.get(k, "")) for k in ("name", "description")).lower()
        if "datasheet" in blob or "data sheet" in blob:
            return True
    return False


def scan_split_text(root: dict) -> bool:
    blob = json.dumps(root, default=str).lower()
    return any(t in blob for t in ("train/test", "training set", "validation set", "test split", "holdout", "train/val"))


def count_split_datasets(entities: List[dict]) -> int:
    n = 0
    for e in entities:
        if not is_dataset(e):
            continue
        name = (str(e.get("name") or "") + " " + " ".join(type_tokens(e))).lower()
        if any(s in name for s in ("training", "validation", "test ", "holdout", " train ", " test")):
            n += 1
    return n


def count_example_records(entities: List[dict]) -> int:
    n = 0
    for e in entities:
        name = str(e.get("name") or "").lower()
        if "example" in name or "sample " in name or name.startswith("sample"):
            n += 1
    return n


def entity_has_env_requirements(entity: dict) -> bool:
    for k in ENV_REQUIREMENT_KEYS:
        if entity.get(k):
            return True
    blob = json.dumps(entity, default=str).lower()
    return any(m in blob for m in CONTAINER_MARKERS)


def _nonempty(value: Any, min_len: int = 1) -> bool:
    """True if a narrative field carries real content of at least min_len chars."""
    if value in (None, "", [], {}):
        return False
    if isinstance(value, list):
        return sum(len(str(v)) for v in value) >= min_len
    return len(str(value).strip()) >= min_len


# ---------------------------------------------------------------------------
# Crate flattening + Evidence snapshot
# ---------------------------------------------------------------------------

def flatten_graph(crate) -> Tuple[List[dict], dict, List[str]]:
    """Return (entities, root_entity, context_namespaces) from a validated
    ROCrateV1_2 or a raw crate dict. Inline sub-crate @graphs (when the
    caller has merged them in) are honored; this function does not read disk.
    """
    if hasattr(crate, "metadataGraph"):
        entities = [e.model_dump(by_alias=True) for e in crate.metadataGraph]
        context = getattr(crate, "context", None)
    else:
        entities = list(crate.get("@graph", []))
        context = crate.get("@context")

    ctx_ns: List[str] = []
    if isinstance(context, dict):
        ctx_ns = [str(v) for v in context.values()]
    elif isinstance(context, list):
        for c in context:
            if isinstance(c, str):
                ctx_ns.append(c)
            elif isinstance(c, dict):
                ctx_ns.extend(str(v) for v in c.values())
    elif isinstance(context, str):
        ctx_ns = [context]

    # Root via the metadata-file descriptor's "about" field; fall back to the
    # first non-descriptor entry (matches v1's behavior).
    descriptor = next((e for e in entities if e.get("@id") == "ro-crate-metadata.json"), None)
    root_id = None
    if descriptor:
        about = descriptor.get("about")
        root_id = about.get("@id") if isinstance(about, dict) else about
    root_entity = next((e for e in entities if e.get("@id") == root_id), None)
    if root_entity is None:
        root_entity = next((e for e in entities if e.get("@id") != "ro-crate-metadata.json"),
                           entities[0] if entities else {})
    return entities, root_entity or {}, ctx_ns


@dataclass
class Evidence:
    """Deterministic snapshot computed once per crate, shared by all 28
    scorers. Counts prefer inline graph walks; release-crate rollups
    (``evi:*`` fields on the root) fill gaps where the graph isn't inline.
    """
    root: dict
    context_namespaces: List[str]
    recognized_standards: List[str]

    # entity counts
    total_entities: int = 0
    dataset_count: int = 0
    software_count: int = 0
    schema_count: int = 0
    computation_count: int = 0
    experiment_count: int = 0
    sub_crate_count: int = 0

    # provenance / computation quality
    datasets_sourced: int = 0
    computation_with_software: int = 0
    computation_with_io: int = 0
    good_computations: int = 0  # software AND inputs AND outputs
    entities_with_provenance_link: int = 0
    sub_crates_linked: int = 0

    # software interpretability
    software_with_link: int = 0
    software_in_archive: int = 0

    # characterization
    tabular_dataset_count: int = 0
    tabular_with_schema: int = 0
    tabular_with_stats: int = 0
    schemas_referencing_standards: int = 0
    ontology_iri_count: int = 0
    datasets_with_description: int = 0

    # verifiability
    hashable_entities: int = 0
    entities_with_hash: int = 0

    # actors
    author_count: int = 0
    authors_with_orcid: int = 0
    has_publisher: bool = False
    publisher_has_ror: bool = False
    has_principal_investigator: bool = False

    # access / computability
    distribution_link_count: int = 0
    distinct_protocols: List[str] = field(default_factory=list)
    api_or_access_documented: bool = False
    datasets_with_accession: int = 0
    published_format_count: int = 0
    proprietary_format_count: int = 0
    software_with_env: int = 0

    # context (6.d)
    split_datasets: int = 0
    split_text: bool = False
    example_records: int = 0

    # narrative / rai flags
    has_datasheet: bool = False
    populated_section_count: int = 0

    def cov(self, num: int, den: int) -> float:
        return (num / den) if den else 0.0


def build_evidence(crate, overrides: Optional[Dict[str, Any]] = None) -> Evidence:
    """Walk the merged graph once and return an Evidence snapshot.

    ``overrides`` lets a caller supply pre-computed coverage metrics keyed by
    Evidence attribute name (e.g. from a full sub-crate walk during a `--deep`
    score). These take precedence over the inline walk and over any stored
    rollup, and are how a release is scored against its sub-crate content
    without writing coverage fields back into the RO-Crate itself — the
    computed numbers live in the AI-Ready score document instead.
    """
    overrides = overrides or {}
    entities, root, ctx_ns = flatten_graph(crate)
    standards = StandardsDetector.detect(ctx_ns)

    ev = Evidence(root=root, context_namespaces=ctx_ns, recognized_standards=standards)
    ev.total_entities = len(entities)

    formats: Counter = Counter()
    protocols: Counter = Counter()
    linked_subcrate_ids = set()
    all_ids = {e.get("@id") for e in entities if e.get("@id")}

    if has_provenance_link(root):
        ev.entities_with_provenance_link += 1

    for e in entities:
        if has_provenance_link(e) and e is not root:
            ev.entities_with_provenance_link += 1

        if is_rocrate(e) and e is not root:
            ev.sub_crate_count += 1
            # linked if referenced from root hasPart / isPartOf graph
            if e.get("@id") and (e.get("isPartOf") or e.get("@id") in _root_part_ids(root)):
                linked_subcrate_ids.add(e.get("@id"))
            continue

        if is_dataset(e):
            ev.dataset_count += 1
            tabular = is_tabular_dataset(e)
            if tabular:
                ev.tabular_dataset_count += 1
            if has_dataset_source(e):
                ev.datasets_sourced += 1
            if _nonempty(e.get("description"), 20):
                ev.datasets_with_description += 1
            if get_dataset_schema_link(e) and tabular:
                ev.tabular_with_schema += 1
            has_stats = bool(e.get("hasSummaryStatistics")) or any(
                e.get(k) is not None for k in ("rowCount", "columnCount", "contentSize", "sampleSize", "size")
            )
            if has_stats and tabular:
                ev.tabular_with_stats += 1
            accs = AccessionDetector.detect(first_present(e, *CONTENT_URL_KEYS))
            if accs:
                ev.datasets_with_accession += 1
            if not is_embargoed(e):
                ev.hashable_entities += 1
                if has_hash(e):
                    ev.entities_with_hash += 1
            url = first_present(e, "contentUrl", "url")
            for u in as_list(url):
                if not isinstance(u, str):
                    continue
                ev.distribution_link_count += 1
                if "://" in u:
                    protocols[u.split("://", 1)[0]] += 1
                if "/api" in u:
                    ev.api_or_access_documented = True
            fmt = get_format(e)
            if fmt:
                formats[str(fmt).strip().lower()] += 1

        elif is_software(e):
            ev.software_count += 1
            ev.hashable_entities += 1
            if has_hash(e):
                ev.entities_with_hash += 1
            link = first_present(e, "url", "codeRepository", "contentUrl")
            if link and (first_present(e, "version", "versionTag") or ArchiveDetector.is_persistent_id(link)):
                ev.software_with_link += 1
            if ArchiveDetector.is_sustainable_archive(link) or ArchiveDetector.is_persistent_id(link):
                ev.software_in_archive += 1
            if entity_has_env_requirements(e):
                ev.software_with_env += 1
            fmt = get_format(e)
            if fmt:
                formats[str(fmt).strip().lower()] += 1

        elif is_schema(e):
            ev.schema_count += 1
            if SchemaStandardDetector.schema_references_standard(e):
                ev.schemas_referencing_standards += 1

        elif is_computation(e):
            ev.computation_count += 1
            has_sw = bool(get_used_software(e))
            has_io = bool(get_inputs(e)) and bool(get_outputs(e))
            if has_sw:
                ev.computation_with_software += 1
            if has_io:
                ev.computation_with_io += 1
            if has_sw and has_io:
                ev.good_computations += 1

        elif is_experiment(e):
            ev.experiment_count += 1

    # Standard release rollups that already live on the RO-Crate model and feed
    # the datasheet (evi:datasetCount, evi:totalEntities, evi:entitiesWithChecksums,
    # …). A release root typically inlines only a handful of housekeeping entities
    # while advertising these counts, so prefer them over the incomplete inline
    # walk. Precedence here: stored rollup when present, else inline tally.
    def pick(inline_val: int, key: str) -> int:
        return _evi_int(root, key) if root.get(key) is not None else inline_val

    ev.dataset_count = pick(ev.dataset_count, "evi:datasetCount")
    ev.software_count = pick(ev.software_count, "evi:softwareCount")
    ev.schema_count = pick(ev.schema_count, "evi:schemaCount")
    ev.computation_count = pick(ev.computation_count, "evi:computationCount")
    ev.total_entities = pick(ev.total_entities, "evi:totalEntities")
    if root.get("evi:entitiesWithChecksums") is not None:
        ev.entities_with_hash = _evi_int(root, "evi:entitiesWithChecksums")
        ev.hashable_entities = ev.dataset_count + ev.software_count

    # v2 coverage metrics. These are NOT stored on the RO-Crate (they'd bloat the
    # model and aren't used by the datasheet). A caller scoring a release supplies
    # them via `overrides` from a full sub-crate walk; the resulting numbers are
    # persisted in the AI-Ready score document, not the crate. When absent, the
    # inline walk's values stand (correct for a single, fully-inlined crate).
    COVERAGE_ATTRS = (
        "dataset_count", "software_count", "schema_count", "computation_count", "total_entities",
        "good_computations", "computation_with_software", "entities_with_provenance_link",
        "software_with_link", "datasets_with_accession", "datasets_sourced",
        "distribution_link_count", "entities_with_hash", "hashable_entities",
        "tabular_dataset_count", "tabular_with_schema", "tabular_with_stats",
    )
    for attr in COVERAGE_ATTRS:
        if attr in overrides and overrides[attr] is not None:
            setattr(ev, attr, overrides[attr])

    ev.ontology_iri_count = OntologyDetector.count(entities)
    ev.split_datasets = count_split_datasets(entities)
    ev.split_text = scan_split_text(root)
    ev.example_records = count_example_records(entities)
    ev.sub_crates_linked = len(linked_subcrate_ids)
    # Distribution protocols: prefer the aggregated set supplied by a deep walk,
    # else the inline walk's schemes.
    if overrides.get("distinct_protocols"):
        ev.distinct_protocols = sorted(set(str(p).lower() for p in as_list(overrides["distinct_protocols"])))
    else:
        ev.distinct_protocols = sorted(protocols.keys())
    ev.published_format_count, ev.proprietary_format_count = _format_buckets(formats)

    # Actors
    ac, orc = author_orcid_coverage(root.get("author"))
    if ac == 0:
        ac = _evi_int(root, "evi:totalAuthors")
        orc = _evi_int(root, "evi:authorsWithOrcid")
    ev.author_count = ac
    ev.authors_with_orcid = orc
    publisher = root.get("publisher")
    ev.has_publisher = _nonempty(publisher)
    ev.publisher_has_ror = publisher_has_ror(publisher)
    ev.has_principal_investigator = _nonempty(root.get("principalInvestigator"))

    # Access narrative
    if _nonempty(root.get("conditionsOfAccess")) or _nonempty(root.get("usageInfo")):
        ev.api_or_access_documented = True

    # Narrative / rai sections
    ev.has_datasheet = find_datasheet_entity(entities)
    section_fields = (
        "rai:dataCollection", "rai:dataUseCases", "rai:dataLimitations", "rai:dataBiases",
        "rai:dataReleaseMaintenancePlan", "rai:personalSensitiveInformation",
    )
    ev.populated_section_count = sum(1 for k in section_fields if _nonempty(root.get(k)))
    if _nonempty(root.get("license") or root.get("dataLicense")):
        ev.populated_section_count += 1

    return ev


def _root_part_ids(root: dict) -> set:
    ids = set()
    for part in as_list(root.get("hasPart")):
        if isinstance(part, dict) and part.get("@id"):
            ids.add(part["@id"])
        elif isinstance(part, str):
            ids.add(part)
    return ids


def _evi_int(root: dict, key: str) -> int:
    v = root.get(key)
    try:
        return int(v) if v is not None else 0
    except (TypeError, ValueError):
        return 0
