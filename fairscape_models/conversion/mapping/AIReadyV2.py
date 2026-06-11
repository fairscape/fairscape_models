"""v2 deterministic AI-Ready RO-Crate grader.

Scores the AI-Ready paper's 7 criteria x 28 sub-criteria on a 0/1/2
(Absent / Partial / Substantive) scale, max 56 points. It is a harsher
sibling of the v1 grader in ``AIReady.py``:

  * No free passes — every rubric earns its score from evidence
    (v1 hard-coded 8 sub-criteria to True).
  * Coverage thresholds, not presence — e.g. a Computation must declare
    inputs AND outputs AND a software link to count; provenance is scored
    as the *fraction* of entities carrying links, not "is there one".
  * ANDs over ORs — e.g. key actors needs author AND publisher.

The human-editable specification for every rule lives in
``AIReadyV2_RULES.md`` next to this file. The thresholds below and the
per-rubric logic implement that document; keep the two in sync.

Entry point: :func:`score_rocrate_v2`. Graph-only — it never reads disk,
so the server's MongoDB path and the CLI can both call it.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from fairscape_models.conversion.models.AIReadyV2 import (
    AIReadyScoreV2, CriterionScoreV2, RubricScoreV2, SCORE_LABELS,
)
from fairscape_models.conversion.mapping import aiready_extract as ax
from fairscape_models.conversion.mapping.aiready_extract import Evidence, build_evidence
from fairscape_models.rocrate import ROCrateV1_2

# --- Tunable thresholds (mirror AIReadyV2_RULES.md) ------------------------
T_SUBSTANTIVE = 0.80   # coverage fraction required for score 2
T_PARTIAL = 0.30       # coverage fraction required for score 1
MIN_DESC_LEN = 200     # root description length (chars) for "detailed" (2.a)
MIN_KEYWORDS = 3       # keyword count for topical coverage (2.a)
MIN_ORCID_FRACTION = 0.30  # author ORCID coverage for substantive actors (1.d)
MIN_NARRATIVE_LEN = 40     # chars for a rai:* narrative to count as non-trivial


# --- helpers ---------------------------------------------------------------

def _mk(rid: str, criterion: str, sub: str, score: int,
        rationale: str, evidence: List[str], gaps: List[str]) -> RubricScoreV2:
    return RubricScoreV2(
        id=rid, criterion=criterion, sub_criterion=sub, score=score,
        label=SCORE_LABELS[score], rationale=rationale,
        evidence=evidence, gaps=[] if score == 2 else gaps,
    )


def _pct(num: int, den: int) -> str:
    return f"{num}/{den} ({(100 * num / den):.0f}%)" if den else f"{num}/0"


def _narr(root: dict, *keys: str) -> bool:
    """A rai/narrative field present with non-trivial length."""
    for k in keys:
        if ax._nonempty(root.get(k), MIN_NARRATIVE_LEN):
            return True
    return False


def _present(root: dict, *keys: str) -> bool:
    return any(ax._nonempty(root.get(k)) for k in keys)


# ============================================================================
# 0 — FAIRness
# ============================================================================

def score_findable(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    pid = ax.ArchiveDetector.is_persistent_id(root.get("identifier") or root.get("@id"))
    archive = bool(ev.root and ax.ArchiveDetector.detect(
        root.get("publisher"), root.get("conditionsOfAccess"),
        root.get("description"), root.get("identifier")))
    evid, gaps = [], []
    if pid:
        evid.append(f"persistent identifier: {root.get('identifier') or root.get('@id')}")
    else:
        gaps.append("no resolvable persistent identifier (DOI/ARK/handle/PURL)")
    if archive:
        evid.append("deposit in a recognized FAIR archive")
    else:
        gaps.append("no recognized FAIR-compliant archive detected")
    score = 2 if (pid and archive) else (1 if (pid or archive) else 0)
    return _mk("0.a", "FAIRness", "Findable", score,
               "Findability requires both a persistent identifier and a recognized archive.",
               evid, gaps)


def score_accessible(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    has_vocab = bool(ev.recognized_standards)
    cl = root.get("confidentialityLevel")
    gated = ax.confidentiality_is_hl7(cl) and str(cl).strip().lower() not in ("unrestricted", "normal", "u", "n")
    access_documented = _present(root, "conditionsOfAccess") or not gated
    evid, gaps = [], []
    if has_vocab:
        evid.append(f"machine-readable metadata in: {', '.join(ev.recognized_standards)}")
    else:
        gaps.append("no recognized JSON-LD vocabulary in @context")
    if gated and not _present(root, "conditionsOfAccess"):
        gaps.append("restricted data but no conditionsOfAccess documented")
    score = 2 if (has_vocab and access_documented) else (1 if has_vocab else 0)
    return _mk("0.b", "FAIRness", "Accessible", score,
               "Metadata must be in a standard vocabulary AND access terms documented when data is gated.",
               evid, gaps)


def score_interoperable(ev: Evidence) -> RubricScoreV2:
    cov = ev.cov(ev.tabular_with_schema, ev.tabular_dataset_count)
    has_std = bool(ev.recognized_standards)
    evid, gaps = [], []
    if has_std:
        evid.append(f"standards in context: {', '.join(ev.recognized_standards)}")
    if ev.tabular_dataset_count:
        evid.append(f"tabular datasets with a schema: {_pct(ev.tabular_with_schema, ev.tabular_dataset_count)}")
    else:
        evid.append("no tabular datasets to schema-link")
    no_tabular = ev.tabular_dataset_count == 0
    if has_std and (cov >= T_SUBSTANTIVE or no_tabular):
        score = 2
    elif has_std or cov >= T_PARTIAL:
        score = 1
        gaps.append(f"link schemas to >= {int(T_SUBSTANTIVE*100)}% of tabular datasets")
    else:
        score = 0
        gaps.append("no schemas and no recognized interoperability standards")
    return _mk("0.c", "FAIRness", "Interoperable", score,
               "Interoperability needs recognized standards AND schema coverage of tabular data.",
               evid, gaps)


def score_reusable(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    lic = root.get("license") or root.get("dataLicense")
    dua = root.get("conditionsOfAccess")
    evid, gaps = [], []
    if ax.is_resolvable_license(lic):
        score = 2
        evid.append(f"resolvable license: {lic}")
    elif ax._nonempty(lic) or ax._nonempty(dua):
        score = 1
        evid.append("license or DUA present but not a resolvable reference")
        gaps.append("provide a resolvable license URL or SPDX identifier")
    else:
        score = 0
        gaps.append("no license and no data-use agreement")
    return _mk("0.d", "FAIRness", "Reusable", score,
               "Reuse terms must be defined via a resolvable license or concrete DUA.",
               evid, gaps)


# ============================================================================
# 1 — Provenance
# ============================================================================

def score_transparent(ev: Evidence) -> RubricScoreV2:
    cov = ev.cov(ev.datasets_sourced, ev.dataset_count)
    evid = [f"datasets naming a source/derivedFrom/accession: {_pct(ev.datasets_sourced, ev.dataset_count)}"]
    gaps = []
    if ev.dataset_count and cov >= T_SUBSTANTIVE:
        score = 2
    elif cov >= T_PARTIAL:
        score = 1
        gaps.append(f"identify sources for >= {int(T_SUBSTANTIVE*100)}% of datasets")
    else:
        score = 0
        gaps.append("most datasets do not identify where they came from")
    return _mk("1.a", "Provenance", "Transparent", score,
               "Substantively all major datasets should resolve to a specific origin.",
               evid, gaps)


def score_traceable(ev: Evidence) -> RubricScoreV2:
    cov = ev.cov(ev.good_computations, ev.computation_count)
    evid = [
        f"computations: {ev.computation_count}",
        f"with software link AND inputs AND outputs: {_pct(ev.good_computations, ev.computation_count)}",
    ]
    gaps = []
    if ev.computation_count and cov >= T_SUBSTANTIVE:
        score = 2
    elif ev.computation_count:
        score = 1
        gaps.append("some computations lack a software link or declared inputs/outputs")
    else:
        score = 0
        gaps.append("no Computation/Activity steps documented")
    return _mk("1.b", "Provenance", "Traceable", score,
               "Each transformation must name its software and declare inputs and outputs.",
               evid, gaps)


def score_interpretable(ev: Evidence) -> RubricScoreV2:
    cov = ev.cov(ev.software_with_link, ev.software_count)
    evid = [
        f"software entities: {ev.software_count}",
        f"with a versioned/resolvable link: {_pct(ev.software_with_link, ev.software_count)}",
        f"in a sustainable archive or pinned: {ev.software_in_archive}",
    ]
    gaps = []
    if ev.software_count and cov >= T_SUBSTANTIVE and ev.software_in_archive > 0:
        score = 2
    elif ev.software_count and cov >= T_PARTIAL:
        score = 1
        gaps.append("pin software to versioned/archived artifacts (Zenodo, Software Heritage, DOI, git tag)")
    else:
        score = 0
        gaps.append("no software, or none carries a resolvable versioned link")
    return _mk("1.c", "Provenance", "Interpretable", score,
               "Software should resolve to versioned artifacts, with the bulk in sustainable archives.",
               evid, gaps)


def score_key_actors(ev: Evidence) -> RubricScoreV2:
    orcid_cov = ev.cov(ev.authors_with_orcid, ev.author_count)
    evid = [
        f"authors: {ev.author_count} (with ORCID: {ev.authors_with_orcid})",
        f"publisher present: {ev.has_publisher}",
        f"principal investigator present: {ev.has_principal_investigator}",
    ]
    gaps = []
    roles_covered = ev.author_count > 0 and ev.has_publisher
    if roles_covered and ev.authors_with_orcid >= 1 and orcid_cov >= MIN_ORCID_FRACTION:
        score = 2
    elif ev.author_count > 0 and (ev.has_publisher or ev.has_principal_investigator):
        score = 1
        gaps.append("add ORCIDs for authors and a ROR for the publishing organization")
    elif ev.author_count > 0:
        score = 1 if ev.author_count > 1 else 0
        gaps.append("identify a publisher and add persistent identifiers (ORCID/ROR)")
    else:
        score = 0
        gaps.append("no actors identified")
    return _mk("1.d", "Provenance", "Key Actors Identified", score,
               "Role coverage (author AND publisher) with a meaningful fraction of ORCIDs.",
               evid, gaps)


# ============================================================================
# 2 — Characterization
# ============================================================================

def score_semantics(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    desc_len = len(str(root.get("description") or ""))
    kw = root.get("keywords")
    kw_count = len(kw) if isinstance(kw, list) else (1 if ax._nonempty(kw) else 0)
    ont = ev.ontology_iri_count
    desc_cov = ev.cov(ev.datasets_with_description, ev.dataset_count)
    evid = [
        f"root description length: {desc_len} chars",
        f"keywords: {kw_count}",
        f"entities carrying ontology IRIs: {ont}",
        f"datasets with their own description: {_pct(ev.datasets_with_description, ev.dataset_count)}",
    ]
    gaps = []
    detailed = desc_len >= MIN_DESC_LEN and kw_count >= MIN_KEYWORDS
    if detailed and ont > 0 and (ev.dataset_count == 0 or desc_cov >= T_PARTIAL):
        score = 2
    elif desc_len > 0 and kw_count >= 1:
        score = 1
        gaps.append("ground subject terms in standard vocabularies (MeSH, EDAM, NCIt, GO)")
        if not detailed:
            gaps.append(f"expand the description (>= {MIN_DESC_LEN} chars) and keywords (>= {MIN_KEYWORDS})")
    else:
        score = 0
        gaps.append("add a detailed description and topical keywords")
    return _mk("2.a", "Characterization", "Semantics", score,
               "Detailed abstract + topical keywords + ontology-grounded subject terms.",
               evid, gaps)


def score_statistics(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    cov = ev.cov(ev.tabular_with_stats, ev.tabular_dataset_count)
    missing_convention = _present(root, "rai:dataCollectionMissingData")
    evid = [
        f"tabular datasets characterized (dims/stats): {_pct(ev.tabular_with_stats, ev.tabular_dataset_count)}",
        f"missing-value convention documented: {missing_convention}",
    ]
    gaps = []
    if ev.tabular_dataset_count == 0:
        # No tabular data — score against what's available, don't punish to 0.
        score = 1 if ev.dataset_count else 0
        evid.append("no tabular datasets present")
        if score < 2:
            gaps.append("non-tabular crate: characterization scored against available content")
    elif cov >= T_SUBSTANTIVE and missing_convention:
        score = 2
    elif cov >= T_PARTIAL or ev.tabular_with_stats > 0:
        score = 1
        gaps.append(f"characterize >= {int(T_SUBSTANTIVE*100)}% of tabular datasets and document missing-value handling")
    else:
        score = 0
        gaps.append("no statistics or dimensions on tabular datasets")
    return _mk("2.b", "Characterization", "Statistics", score,
               "Most tabular datasets characterized + missing-value convention documented.",
               evid, gaps)


def score_standards(ev: Evidence) -> RubricScoreV2:
    cov = ev.cov(ev.schemas_referencing_standards, ev.schema_count)
    evid = [f"schemas referencing a recognized standard: {_pct(ev.schemas_referencing_standards, ev.schema_count)}"]
    gaps = []
    if ev.schema_count and cov >= T_SUBSTANTIVE:
        score = 2
    elif ev.schema_count:
        score = 1
        gaps.append("reference recognized standards (JSON Schema, Frictionless, LOINC, OMOP) from schemas")
    else:
        score = 0
        gaps.append("no Schema entities present")
    return _mk("2.c", "Characterization", "Standards", score,
               "Schemas should reference recognized data standards.",
               evid, gaps)


def score_bias(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    val = root.get("rai:dataBiases")
    evid, gaps = [], []
    if _narr(root, "rai:dataBiases"):
        score = 2
        evid.append("rai:dataBiases documented")
    elif ax._nonempty(val):
        score = 1
        evid.append("rai:dataBiases present but brief")
        gaps.append("expand the bias description")
    else:
        score = 0
        gaps.append("document potential sources of bias (rai:dataBiases)")
    return _mk("2.d", "Characterization", "Potential Sources of Bias", score,
               "Known biases should be described substantively.",
               evid, gaps)


def score_data_quality(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    coll = _present(root, "rai:dataCollection")
    miss = _present(root, "rai:dataCollectionMissingData")
    evid = [f"rai:dataCollection: {coll}", f"rai:dataCollectionMissingData: {miss}"]
    gaps = []
    if coll and miss:
        score = 2
    elif coll or miss:
        score = 1
        gaps.append("document both data collection and missing-data handling")
    else:
        score = 0
        gaps.append("document data collection methodology and missing-data handling")
    return _mk("2.e", "Characterization", "Data Quality", score,
               "Both collection methodology and missing-data handling should be documented.",
               evid, gaps)


# ============================================================================
# 3 — Pre-Model Explainability
# ============================================================================

def score_data_documentation(ev: Evidence) -> RubricScoreV2:
    n = ev.populated_section_count + (1 if ev.has_datasheet else 0)
    evid = [
        f"populated documentation sections: {ev.populated_section_count}/7",
        f"datasheet entity present: {ev.has_datasheet}",
    ]
    gaps = []
    if n >= 6:
        score = 2
    elif n >= 2:
        score = 1
        gaps.append("populate the remaining datasheet sections (collection, use-cases, limitations, biases, governance, sensitive-info, license)")
    else:
        score = 0
        gaps.append("provide a structured datasheet covering the standard sections")
    return _mk("3.a", "Pre-Model Explainability", "Data Documentation Template", score,
               "A documentation template should populate the standard datasheet sections.",
               evid, gaps)


def score_fit_for_purpose(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    uc = _narr(root, "rai:dataUseCases")
    lim = _narr(root, "rai:dataLimitations")
    evid = [f"use cases: {uc}", f"limitations: {lim}"]
    gaps = []
    if uc and lim:
        score = 2
    elif uc or lim:
        score = 1
        gaps.append("document both intended use cases and limitations")
    else:
        score = 0
        gaps.append("document intended use cases (rai:dataUseCases) and limitations (rai:dataLimitations)")
    return _mk("3.b", "Pre-Model Explainability", "Fit For Purpose", score,
               "Both use cases and limitations should be documented.",
               evid, gaps)


def score_verifiable(ev: Evidence) -> RubricScoreV2:
    cov = ev.cov(ev.entities_with_hash, ev.hashable_entities)
    evid = [f"Dataset/Software entities with a checksum (embargo excluded): {_pct(ev.entities_with_hash, ev.hashable_entities)}"]
    gaps = []
    if ev.hashable_entities and cov >= T_SUBSTANTIVE:
        score = 2
    elif cov >= T_PARTIAL:
        score = 1
        gaps.append(f"add SHA-256/MD5 to >= {int(T_SUBSTANTIVE*100)}% of datasets and software")
    else:
        score = 0
        gaps.append("no checksums on datasets or software")
    return _mk("3.c", "Pre-Model Explainability", "Verifiable", score,
               "Substantively all datasets and software should carry a cryptographic hash.",
               evid, gaps)


# ============================================================================
# 4 — Ethics
# ============================================================================

def score_ethically_acquired(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    coll = _present(root, "rai:dataCollection")
    ethics_signal = _present(root, "ethicalReview", "humanSubjectResearch") or ax.scan_irb_refs(root)
    evid = [f"collection narrative: {coll}", f"ethics/IRB signal: {ethics_signal}"]
    gaps = []
    if coll and ethics_signal:
        score = 2
    elif coll or ethics_signal:
        score = 1
        gaps.append("document both collection methodology and ethical review/IRB")
    else:
        score = 0
        gaps.append("document how data was acquired and its ethical review")
    return _mk("4.a", "Ethics", "Ethically Acquired", score,
               "Collection methodology AND an ethics/IRB signal.",
               evid, gaps)


def score_ethically_managed(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    gov = _present(root, "dataGovernanceCommittee", "ethicalReview") or \
        ax.get_additional_property(root, "Data Governance Committee") is not None
    sens = _present(root, "rai:personalSensitiveInformation")
    evid = [f"governance/ethical-review: {bool(gov)}", f"sensitive-info handling: {sens}"]
    gaps = []
    if gov and sens:
        score = 2
    elif gov or sens:
        score = 1
        gaps.append("document both governance oversight and sensitive-information handling")
    else:
        score = 0
        gaps.append("document data governance and personal/sensitive information")
    return _mk("4.b", "Ethics", "Ethically Managed", score,
               "Governance oversight AND sensitive-information handling.",
               evid, gaps)


def score_ethically_disseminated(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    lic = ax.is_resolvable_license(root.get("license") or root.get("dataLicense"))
    controls = (_present(root, "conditionsOfAccess", "rai:personalSensitiveInformation", "contactEmail")
                or ax.get_additional_property(root, "Prohibited Uses") is not None)
    evid = [f"resolvable license: {lic}", f"dissemination control present: {bool(controls)}"]
    gaps = []
    if lic and controls:
        score = 2
    elif lic or _present(root, "license", "dataLicense"):
        score = 1
        gaps.append("add access conditions, sensitive-info handling, or a contact for enforcement")
    else:
        score = 0
        gaps.append("specify a license and dissemination controls")
    return _mk("4.c", "Ethics", "Ethically Disseminated", score,
               "Resolvable license AND at least one dissemination control.",
               evid, gaps)


def score_secure(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    cl = root.get("confidentialityLevel")
    hl7 = ax.confidentiality_is_hl7(cl)
    security_signal = root.get("deidentified") is not None or _present(root, "rai:personalSensitiveInformation")
    evid = [f"confidentialityLevel HL7-coded: {hl7}", f"security signal (deidentified/sensitive-info): {bool(security_signal)}"]
    gaps = []
    if hl7 and security_signal:
        score = 2
    elif ax._nonempty(cl):
        score = 1
        gaps.append("use an HL7 confidentiality code and set deidentified / sensitive-info fields")
    else:
        score = 0
        gaps.append("declare a confidentialityLevel (HL7 code)")
    return _mk("4.d", "Ethics", "Secure", score,
               "HL7 confidentiality code AND a concrete security signal.",
               evid, gaps)


# ============================================================================
# 5 — Sustainability
# ============================================================================

def score_persistent(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    pid = ax.ArchiveDetector.is_persistent_id(root.get("identifier") or root.get("@id"))
    archive = bool(ax.ArchiveDetector.detect(root.get("publisher"), root.get("identifier"), root.get("conditionsOfAccess")))
    evid, gaps = [], []
    if pid:
        evid.append("persistent identifier pattern present")
    else:
        gaps.append("mint a persistent identifier (DOI/ARK/handle)")
    if archive:
        evid.append("archival host detected")
    else:
        gaps.append("deposit in a recognized archive")
    score = 2 if (pid and archive) else (1 if (pid or archive) else 0)
    return _mk("5.a", "Sustainability", "Persistent", score,
               "Persistent identifier AND archival hosting.",
               evid, gaps)


def score_domain_appropriate(ev: Evidence) -> RubricScoreV2:
    cov = ev.cov(ev.datasets_with_accession, ev.dataset_count)
    evid = [f"datasets with specialist-repo accessions: {_pct(ev.datasets_with_accession, ev.dataset_count)}"]
    gaps = []
    if ev.datasets_with_accession and cov >= T_SUBSTANTIVE:
        score = 2
    elif ev.datasets_with_accession:
        score = 1
        gaps.append("deposit major datasets in domain-appropriate specialist repositories (GEO, SRA, PRIDE, dbGaP)")
    else:
        score = 0
        gaps.append("no specialist-repository accessions detected")
    return _mk("5.b", "Sustainability", "Domain Appropriate", score,
               "Major datasets should live in domain-appropriate specialist repositories.",
               evid, gaps)


def score_well_governed(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    plan = _present(root, "rai:dataReleaseMaintenancePlan")
    party = (_present(root, "dataGovernanceCommittee", "principalInvestigator", "contactEmail")
             or ax.get_additional_property(root, "Data Governance Committee") is not None)
    evid = [f"maintenance plan: {plan}", f"responsible party: {bool(party)}"]
    gaps = []
    if plan and party:
        score = 2
    elif plan or party:
        score = 1
        gaps.append("document both a maintenance plan and a responsible party")
    else:
        score = 0
        gaps.append("document a release/maintenance plan and a governing party")
    return _mk("5.c", "Sustainability", "Well-Governed", score,
               "Maintenance plan AND an identified responsible party.",
               evid, gaps)


def score_associated(ev: Evidence) -> RubricScoreV2:
    cov = ev.cov(ev.entities_with_provenance_link, ev.total_entities)
    subcrates_ok = ev.sub_crate_count == 0 or ev.sub_crates_linked >= ev.sub_crate_count
    evid = [
        f"entities with a provenance link: {_pct(ev.entities_with_provenance_link, ev.total_entities)}",
        f"sub-crates linked from parent: {ev.sub_crates_linked}/{ev.sub_crate_count}",
    ]
    gaps = []
    if cov >= T_SUBSTANTIVE and subcrates_ok:
        score = 2
    elif cov >= T_PARTIAL:
        score = 1
        if not subcrates_ok:
            gaps.append("link all sub-crates back to the parent release")
        gaps.append(f"raise provenance-link coverage to >= {int(T_SUBSTANTIVE*100)}%")
    else:
        score = 0
        gaps.append("components are a flat list with no derivedFrom/generatedBy/used* edges")
    return _mk("5.d", "Sustainability", "Associated", score,
               "Components densely connected via provenance edges; sub-crates linked.",
               evid, gaps)


# ============================================================================
# 6 — Computability
# ============================================================================

def score_standardized(ev: Evidence) -> RubricScoreV2:
    root = ev.root
    conforms = _present(root, "conformsTo")
    standards = bool(ev.recognized_standards) or ev.schemas_referencing_standards > 0
    evid = [f"conformsTo declared: {conforms}", f"recognized standards/schema refs: {standards}"]
    gaps = []
    if conforms and standards:
        score = 2
    elif conforms or standards:
        score = 1
        gaps.append("declare conformsTo AND reference recognized standards")
    else:
        score = 0
        gaps.append("declare standards conformance (conformsTo) and reference recognized standards")
    return _mk("6.a", "Computability", "Standardized", score,
               "conformsTo declaration AND recognized standards references.",
               evid, gaps)


def score_computationally_accessible(ev: Evidence) -> RubricScoreV2:
    standard_protocol = any(p in ("http", "https", "ftp", "s3", "gs") for p in ev.distinct_protocols)
    evid = [
        f"distribution links: {ev.distribution_link_count}",
        f"protocols: {', '.join(ev.distinct_protocols) or 'none'}",
        f"API/access documented: {ev.api_or_access_documented}",
    ]
    gaps = []
    if ev.distribution_link_count and standard_protocol and ev.api_or_access_documented:
        score = 2
    elif ev.distribution_link_count:
        score = 1
        gaps.append("document the access/request procedure or expose a standard-protocol endpoint")
    else:
        score = 0
        gaps.append("no resolvable distribution links, API, or access instructions")
    return _mk("6.b", "Computability", "Computationally Accessible", score,
               "Standard-protocol distribution AND documented access for gated data.",
               evid, gaps)


def score_portable(ev: Evidence) -> RubricScoreV2:
    total_fmt = ev.published_format_count + ev.proprietary_format_count
    common_cov = (ev.published_format_count / total_fmt) if total_fmt else 0.0
    sw_env_cov = ev.cov(ev.software_with_env, ev.software_count)
    evid = [
        f"published/common formats: {ev.published_format_count} (proprietary: {ev.proprietary_format_count})",
        f"software with documented environment: {_pct(ev.software_with_env, ev.software_count)}",
    ]
    gaps = []
    formats_ok = total_fmt == 0 or common_cov >= T_SUBSTANTIVE
    env_ok = ev.software_count == 0 or sw_env_cov >= T_PARTIAL
    if formats_ok and env_ok and (ev.software_count == 0 or ev.software_with_env > 0):
        score = 2 if total_fmt or ev.software_count else 1
    elif formats_ok:
        score = 1
        gaps.append("document compute environment/containers for software that needs it")
    else:
        score = 0
        gaps.append("formats are proprietary/unspecified and environment is undocumented")
    return _mk("6.c", "Computability", "Portable", score,
               "Widely-readable formats AND documented compute environment for software.",
               evid, gaps)


def score_contextualized(ev: Evidence) -> RubricScoreV2:
    splits = ev.split_datasets > 0 or ev.split_text
    examples = ev.example_records > 0
    withheld = ev.split_text  # split/withholding language scanned together
    signals = sum([splits, examples, withheld])
    evid = [
        f"split datasets/text: {ev.split_datasets}/{ev.split_text}",
        f"example records: {ev.example_records}",
    ]
    gaps = []
    if splits and examples:
        score = 2
    elif signals >= 1:
        score = 1
        gaps.append("document train/test/validation splits AND provide example records")
    else:
        score = 0
        gaps.append("no split discussion, withheld-information notes, or example records")
    return _mk("6.d", "Computability", "Contextualized", score,
               "Splits explicit AND example records / withholding documented.",
               evid, gaps)


# ============================================================================
# Registry + entry point
# ============================================================================

# Ordered: each tuple is (criterion name, [scorer functions]).
_CRITERIA = [
    ("FAIRness", [score_findable, score_accessible, score_interoperable, score_reusable]),
    ("Provenance", [score_transparent, score_traceable, score_interpretable, score_key_actors]),
    ("Characterization", [score_semantics, score_statistics, score_standards, score_bias, score_data_quality]),
    ("Pre-Model Explainability", [score_data_documentation, score_fit_for_purpose, score_verifiable]),
    ("Ethics", [score_ethically_acquired, score_ethically_managed, score_ethically_disseminated, score_secure]),
    ("Sustainability", [score_persistent, score_domain_appropriate, score_well_governed, score_associated]),
    ("Computability", [score_standardized, score_computationally_accessible, score_portable, score_contextualized]),
]


def score_rocrate_v2(
    crate_data: Union[Dict[str, Any], ROCrateV1_2],
    aggregate_metrics: Optional[Dict[str, Any]] = None,
) -> AIReadyScoreV2:
    """Score an RO-Crate (or already-merged release graph) deterministically.

    Args:
        crate_data: a parsed RO-Crate dict or a validated ROCrateV1_2. A dict
            is validated through ROCrateV1_2 (same front door as v1); pass a
            dict whose @graph already contains merged sub-crate entities to
            score a full release.
        aggregate_metrics: optional pre-computed coverage metrics keyed by
            Evidence attribute name (e.g. from a full sub-crate walk). These
            override the inline walk so a release scores against its sub-crate
            content. They are echoed back in the result's ``evidence`` field
            rather than written onto the crate.

    Returns:
        AIReadyScoreV2 with all 28 rubrics scored and aggregated, plus the
        coverage ``evidence`` it was computed from.
    """
    if isinstance(crate_data, dict):
        crate = ROCrateV1_2.model_validate(crate_data)
    else:
        crate = crate_data

    ev = build_evidence(crate, overrides=aggregate_metrics)
    root_name = ev.root.get("name") or "RO-Crate"

    criteria: List[CriterionScoreV2] = []
    total_earned = 0
    total_possible = 0
    for crit_name, scorers in _CRITERIA:
        rubrics = [fn(ev) for fn in scorers]
        earned = sum(r.score for r in rubrics)
        possible = 2 * len(rubrics)
        total_earned += earned
        total_possible += possible
        criteria.append(CriterionScoreV2(
            criterion=crit_name, rubrics=rubrics,
            earned=earned, possible=possible,
            percentage=round(100 * earned / possible, 1) if possible else 0.0,
        ))

    return AIReadyScoreV2(
        name=f"AI-Ready Score v2 for {root_name}",
        criteria=criteria,
        total_earned=total_earned,
        total_possible=total_possible,
        percentage=round(100 * total_earned / total_possible, 1) if total_possible else 0.0,
        evidence=_evidence_dict(ev),
    )


def _evidence_dict(ev: Evidence) -> Dict[str, Any]:
    """The coverage counts the score was computed from — stored in the score
    document so it's auditable without re-walking the crate."""
    return {
        "total_entities": ev.total_entities,
        "dataset_count": ev.dataset_count,
        "software_count": ev.software_count,
        "schema_count": ev.schema_count,
        "computation_count": ev.computation_count,
        "sub_crate_count": ev.sub_crate_count,
        "sub_crates_linked": ev.sub_crates_linked,
        "datasets_sourced": ev.datasets_sourced,
        "good_computations": ev.good_computations,
        "computation_with_software": ev.computation_with_software,
        "computation_with_io": ev.computation_with_io,
        "entities_with_provenance_link": ev.entities_with_provenance_link,
        "software_with_link": ev.software_with_link,
        "software_in_archive": ev.software_in_archive,
        "tabular_dataset_count": ev.tabular_dataset_count,
        "tabular_with_schema": ev.tabular_with_schema,
        "tabular_with_stats": ev.tabular_with_stats,
        "schemas_referencing_standards": ev.schemas_referencing_standards,
        "ontology_iri_count": ev.ontology_iri_count,
        "hashable_entities": ev.hashable_entities,
        "entities_with_hash": ev.entities_with_hash,
        "author_count": ev.author_count,
        "authors_with_orcid": ev.authors_with_orcid,
        "datasets_with_accession": ev.datasets_with_accession,
        "distribution_link_count": ev.distribution_link_count,
        "distinct_protocols": ev.distinct_protocols,
        "published_format_count": ev.published_format_count,
        "proprietary_format_count": ev.proprietary_format_count,
        "software_with_env": ev.software_with_env,
        "populated_section_count": ev.populated_section_count,
    }
