# AI-Ready v2 Deterministic Grader — Rules Specification

This document is the **human-editable source of truth** for the v2
deterministic AI-Ready grader. It describes every threshold and every
per-rubric 0/1/2 rule in prose. The implementation lives in
`AIReadyV2.py` (scorers) and `aiready_extract.py` (evidence). When you
edit this file and want the code regenerated to match, hand this file to
Claude and say "update `AIReadyV2.py` to match `AIReadyV2_RULES.md`".

**Design intent.** v2 is deliberately harsher than v1. Three principles:

1. **No free passes.** Every rubric earns its score from evidence. (v1
   hard-coded 8 sub-criteria to always-pass.)
2. **Coverage, not presence.** A rubric scores 2 only when *most* of the
   relevant entities satisfy it — not when a single one does.
3. **ANDs over ORs.** Where v1 accepted "author OR publisher", v2 wants
   both, plus identifiers.

A deterministic grader cannot judge semantic quality (is this description
*good*?). It uses computable proxies — description length, keyword count,
ontology-IRI presence, coverage ratios.

---

## Scale

Each of the 28 sub-criteria scores **0 (Absent) / 1 (Partial) / 2
(Substantive)**. Seven criteria group the 28 rubrics. Maximum = **56**.
Overall percentage = `total_earned / 56`.

| # | Criterion | Rubrics | Max |
|---|-----------|---------|-----|
| 0 | FAIRness | 0.a–0.d (4) | 8 |
| 1 | Provenance | 1.a–1.d (4) | 8 |
| 2 | Characterization | 2.a–2.e (5) | 10 |
| 3 | Pre-Model Explainability | 3.a–3.c (3) | 6 |
| 4 | Ethics | 4.a–4.d (4) | 8 |
| 5 | Sustainability | 5.a–5.d (4) | 8 |
| 6 | Computability | 6.a–6.d (4) | 8 |

---

## Running the grader

**Single crate** (one fully-inlined `ro-crate-metadata.json`):

```bash
fairscape-cli rocrate score <crate-dir-or-metadata.json> --grader-version v2
```

**Release crate** (a directory of sub-crates — use `--deep` so coverage is
measured against the sub-crate content, not the thin release root):

```bash
fairscape-cli rocrate score <release-dir> --grader-version v2 --deep
```

**Write the full score document** (all 28 rubric scores + rationales +
gaps + the `evidence` coverage block) to a file:

```bash
fairscape-cli rocrate score <release-dir> --grader-version v2 --deep \
    --json <release-dir>/ai_ready_score_v2.json
```

What each step runs, concretely:

1. Load `ro-crate-metadata.json` from the path (directory or file).
2. If `--deep`: walk every `**/ro-crate-metadata.json` under the release
   dir via `collect_subcrate_aggregated_metrics`
   (`fairscape-cli/.../models/rocrate.py`), producing the coverage counts.
   `_deep_coverage_metrics` (`rocrate_commands.py`) maps them to a dict
   keyed by `Evidence` attribute name. The crate file is **not** modified.
3. `score_rocrate_v2(crate_dict, aggregate_metrics=<dict>)`
   (`AIReadyV2.py`) builds the `Evidence` snapshot (overrides > stored
   datasheet `evi:*` > inline walk), runs the 28 scorers, aggregates by
   criterion, and returns `AIReadyScoreV2`.
4. The result — including the `evidence` counts the score came from — is
   printed as a table or written to `--json`.

Equivalent Python:

```python
import json
from fairscape_models.conversion.mapping.AIReadyV2 import score_rocrate_v2

crate = json.load(open("CM4AIJuneRelease/ro-crate-metadata.json"))
score = score_rocrate_v2(crate)                       # single crate
# score = score_rocrate_v2(crate, aggregate_metrics=m)  # release (m from the walk)
print(score.total_earned, "/", score.total_possible, score.percentage, "%")
```

The June 2026 CM4AI release scores **42/56 = 75.0%** via the `--deep` path;
the written document is `CM4AIJuneRelease/ai_ready_score_v2.json`.

---

## Tunable thresholds

These are module-level constants in `AIReadyV2.py`. Change them here,
then in the code (or ask Claude to sync).

| Constant | Default | Meaning |
|----------|---------|---------|
| `T_SUBSTANTIVE` | `0.80` | Coverage fraction required to score **2** on coverage rubrics |
| `T_PARTIAL` | `0.30` | Coverage fraction required to score **1** on coverage rubrics |
| `MIN_DESC_LEN` | `200` | Root description length (chars) to count as "detailed" (2.a) |
| `MIN_KEYWORDS` | `3` | Keyword count for topical coverage (2.a) |
| `MIN_ORCID_FRACTION` | `0.30` | Author ORCID coverage for substantive actors (1.d) |
| `MIN_NARRATIVE_LEN` | `40` | Chars for a `rai:*` narrative to count as non-trivial |

Notation below: `cov(x, n) = x / n` (0 when `n = 0`).

---

## 0 — FAIRness

### 0.a Findable
Evidence: `pid` = root `identifier`/`@id` matches a persistent-ID pattern
(`doi.org`, `hdl.handle.net`, `n2t.net`, `ark:`, `purl.org`); `archive` =
a recognized FAIR archive hostname appears in publisher / identifier /
conditionsOfAccess / description.
- **2**: `pid` AND `archive`.
- **1**: `pid` OR `archive`.
- **0**: neither.

### 0.b Accessible
Evidence: `has_vocab` = a recognized vocabulary in `@context`
(schema.org, EVI, DCAT, Croissant, …); `access_documented` = data is open
(confidentiality not gated) OR `conditionsOfAccess` is present.
- **2**: `has_vocab` AND `access_documented`.
- **1**: `has_vocab` but gated data with no access terms.
- **0**: no recognized vocabulary.

### 0.c Interoperable
Evidence: `schema_cov = cov(tabular_with_schema, tabular_dataset_count)`;
`has_std` = recognized interoperability standards in context.
- **2**: `has_std` AND (`schema_cov >= T_SUBSTANTIVE` OR there are 0
  tabular datasets — nothing to schema-link).
- **1**: `has_std` OR `schema_cov >= T_PARTIAL`.
- **0**: no schemas and no standards.

### 0.d Reusable
Evidence: resolvable license = URL or SPDX prefix (`cc-`, `cc0`, `mit`,
`apache`, `gpl`, `bsd`, `mpl`, `lgpl`, `0bsd`).
- **2**: resolvable license.
- **1**: a free-text license OR a DUA narrative, but not resolvable.
- **0**: no license, no DUA.

---

## 1 — Provenance

### 1.a Transparent
Evidence: a Dataset is "sourced" if it declares `wasDerivedFrom` /
`derivedFrom` / `isBasedOn`, OR `generatedBy` / `wasGeneratedBy` (a
Computation that produced the dataset is just as resolvable an origin as
a source dataset), OR its `contentUrl` carries a specialist-repo
accession. `cov = cov(datasets_sourced, dataset_count)`.
- **2**: `cov >= T_SUBSTANTIVE`.
- **1**: `cov >= T_PARTIAL`.
- **0**: below `T_PARTIAL`.

### 1.b Traceable  *(key v2 improvement)*
Evidence: a "good" Computation declares a **software link AND inputs AND
outputs**. `cov = cov(good_computations, computation_count)`.
- **2**: `computation_count > 0` AND `cov >= T_SUBSTANTIVE`.
- **1**: computations exist but coverage below substantive (coarse steps,
  missing software links, or missing I/O).
- **0**: no computations, or all are bare stubs.

### 1.c Interpretable
Evidence: `software_with_link` = Software with a versioned/resolvable
link; `software_in_archive` = link in a sustainable archive (Zenodo,
Software Heritage, Figshare, OSF, Dryad, DOI) or persistent-ID pinned.
`cov = cov(software_with_link, software_count)`.
- **2**: `software_count > 0` AND `cov >= T_SUBSTANTIVE` AND
  `software_in_archive > 0`.
- **1**: software present, links fragile or partial (`cov >= T_PARTIAL`).
- **0**: no software, or none has a resolvable versioned link.

### 1.d Key Actors Identified  *(OR → AND)*
Evidence: `author_count`, `authors_with_orcid`, `has_publisher`,
`has_principal_investigator`; `orcid_cov = cov(authors_with_orcid,
author_count)`.
- **2**: author AND publisher present AND `authors_with_orcid >= 1` AND
  `orcid_cov >= MIN_ORCID_FRACTION`. (Per the paper, treat partial ORCID
  coverage as fine — missing identifiers are assumed to belong to people
  without one.)
- **1**: named actors with role coverage but ~no identifiers; OR a single
  author with no publisher but more than one named author.
- **0**: single plain-string author / none.

---

## 2 — Characterization

### 2.a Semantics
Evidence: `desc_len` (root description chars), `keyword_count`,
`ontology_iri_count` (entities carrying MeSH/OBO/EDAM/NCIt/GO IRIs),
`desc_cov = cov(datasets_with_description, dataset_count)`.
- **2**: `desc_len >= MIN_DESC_LEN` AND `keyword_count >= MIN_KEYWORDS`
  AND `ontology_iri_count > 0` AND (no datasets OR `desc_cov >=
  T_PARTIAL`).
- **1**: description and >= 1 keyword present, but free-text only (no
  ontology grounding) or thin.
- **0**: one-line/generic description, no keywords.

### 2.b Statistics
Evidence: `cov = cov(tabular_with_stats, tabular_dataset_count)` where a
tabular Dataset is "characterized" if it links `hasSummaryStatistics` or
carries `rowCount`/`columnCount`/`contentSize`/`sampleSize`;
`missing_convention` = `rai:dataCollectionMissingData` present.
- **No tabular datasets**: score **1** if any datasets exist (characterize
  against available content), else **0** — never punished to 0 for being
  image/binary-heavy.
- **2**: `cov >= T_SUBSTANTIVE` AND `missing_convention`.
- **1**: some coverage (`cov >= T_PARTIAL` or any stats present).
- **0**: no statistics on tabular datasets.

### 2.c Standards
Evidence: `cov = cov(schemas_referencing_standards, schema_count)` (a
schema references a standard via JSON Schema `$schema`, Frictionless keys,
LOINC/OMOP/GA4GH/FHIR/DataCite/DCAT strings, or `conformsTo`).
- **2**: `schema_count > 0` AND `cov >= T_SUBSTANTIVE`.
- **1**: schemas exist, few reference standards.
- **0**: no Schema entities.

### 2.d Potential Sources of Bias
Evidence: `rai:dataBiases`.
- **2**: present and non-trivial (`>= MIN_NARRATIVE_LEN` chars).
- **1**: present but brief.
- **0**: absent.

### 2.e Data Quality
Evidence: `rai:dataCollection`, `rai:dataCollectionMissingData`.
- **2**: both present.
- **1**: one present.
- **0**: neither.

---

## 3 — Pre-Model Explainability

### 3.a Data Documentation Template
Evidence: count of populated documentation sections (the six `rai:*`
fields `dataCollection`, `dataUseCases`, `dataLimitations`, `dataBiases`,
`dataReleaseMaintenancePlan`, `personalSensitiveInformation`, plus a
license) and whether a datasheet entity exists. `n = populated_sections +
(1 if datasheet)`.
- **2**: `n >= 6`.
- **1**: `2 <= n <= 5`.
- **0**: `n <= 1`.

### 3.b Fit For Purpose  *(OR → AND)*
Evidence: `rai:dataUseCases`, `rai:dataLimitations` (non-trivial).
- **2**: both present.
- **1**: one.
- **0**: neither.

### 3.c Verifiable  *(coverage)*
Evidence: `cov = cov(entities_with_hash, hashable_entities)` over
Datasets + Software; embargoed datasets excluded from the denominator.
- **2**: `cov >= T_SUBSTANTIVE`.
- **1**: `cov >= T_PARTIAL` (e.g. datasets hashed but not software).
- **0**: no checksums.

---

## 4 — Ethics

### 4.a Ethically Acquired
Evidence: `rai:dataCollection` AND an ethics signal (`ethicalReview`,
`humanSubjectResearch`, or an IRB/protocol reference).
- **2**: collection narrative AND ethics signal.
- **1**: one.
- **0**: none.

### 4.b Ethically Managed
Evidence: governance (`dataGovernanceCommittee`/`ethicalReview` or a
"Data Governance Committee" additionalProperty) AND
`rai:personalSensitiveInformation`.
- **2**: both.
- **1**: one.
- **0**: none.

### 4.c Ethically Disseminated  *(OR → AND)*
Evidence: resolvable license AND >= 1 dissemination control
(`conditionsOfAccess`, `rai:personalSensitiveInformation`, `contactEmail`,
or a "Prohibited Uses" additionalProperty).
- **2**: resolvable license AND a control.
- **1**: any license present (even non-resolvable) but no control.
- **0**: none.

### 4.d Secure
Evidence: `confidentialityLevel` is an HL7 code (`unrestricted`/`normal`/
`restricted`/`very restricted`/`u`/`n`/`r`/`v`) AND a security signal
(`deidentified` set, or `rai:personalSensitiveInformation`).
- **2**: HL7 code AND security signal.
- **1**: a free-text confidentiality value only.
- **0**: none.

---

## 5 — Sustainability

### 5.a Persistent
Evidence: persistent-ID pattern on the identifier AND an archival host.
- **2**: both.
- **1**: one.
- **0**: neither.

### 5.b Domain Appropriate
Evidence: `cov = cov(datasets_with_accession, dataset_count)` — Datasets
whose `contentUrl` carries a specialist-repo accession (GEO, SRA, PRIDE,
MassIVE, BioStudies, dbGaP, EGA, ENA, ArrayExpress).
- **2**: `cov >= T_SUBSTANTIVE`.
- **1**: some accessions present.
- **0**: none.

### 5.c Well-Governed  *(OR → AND)*
Evidence: `rai:dataReleaseMaintenancePlan` AND a responsible party
(`dataGovernanceCommittee`, `principalInvestigator`, `contactEmail`, or a
governance additionalProperty).
- **2**: plan AND party.
- **1**: one.
- **0**: none.

### 5.d Associated  *(was hard-True in v1; now coverage)*
Evidence: `cov = cov(entities_with_provenance_link, total_entities)`;
`subcrates_ok` = no sub-crates OR all sub-crates linked from the parent.
- **2**: `cov >= T_SUBSTANTIVE` AND `subcrates_ok`.
- **1**: `cov >= T_PARTIAL` (thin / some orphans).
- **0**: flat `hasPart` only, no provenance edges.

---

## 6 — Computability

### 6.a Standardized
Evidence: `conformsTo` declared AND recognized standards/schema references
present.
- **2**: both.
- **1**: one.
- **0**: none.

### 6.b Computationally Accessible  *(OR → AND)*
Evidence: `distribution_link_count`; `standard_protocol` = a protocol in
{http, https, ftp, s3, gs}; `api_or_access_documented` = an `/api` link,
`conditionsOfAccess`, or `usageInfo`.
- **2**: links present AND standard protocol AND access documented.
- **1**: links present but single-mechanism / undocumented access.
- **0**: no resolvable links, API, or access instructions.

### 6.c Portable  *(was hard-True in v1)*
Evidence: `common_cov` = published / (published + proprietary) format
share; `sw_env_cov = cov(software_with_env, software_count)` where env =
container reference (docker/singularity/apptainer/ghcr/quay) or a
requirements field.
- **2**: formats widely-readable (`common_cov >= T_SUBSTANTIVE` or no
  formats declared) AND software environment documented where software
  exists.
- **1**: common formats but environment undocumented.
- **0**: proprietary/unspecified formats, no environment.

### 6.d Contextualized  *(was hard-True in v1)*
Evidence: `splits` = split Datasets or split language in root text;
`examples` = example/sample record entities; `withheld` = withholding
language in root text.
- **2**: `splits` AND `examples`.
- **1**: at least one of splits / examples / withheld.
- **0**: none.

---

## Release crates (the `--deep` walk)

A release crate inlines only a handful of housekeeping entities while its
real content (datasets, computations, URLs) lives in sub-crates. Coverage
rubrics must be measured against that sub-crate content, not the thin
release root.

**Where the numbers live.** The coverage metrics are *not* written onto
the RO-Crate — that would bloat `ROCrateMetadataElem` with fields the
datasheet never reads. Instead they are computed at scoring time and
stored in the **AI-Ready score document** (`AIReadyScoreV2.evidence`), so
the score is self-contained and auditable without re-walking the crate.

**How.** Score a release with
`fairscape-cli rocrate score <release-dir> --grader-version v2 --deep`.
`--deep` walks every sub-crate from disk via
`collect_subcrate_aggregated_metrics`, builds a dict of coverage metrics
keyed by `Evidence` attribute name, and passes it to
`score_rocrate_v2(crate, aggregate_metrics=...)`. Those values override the
inline walk and are echoed into the result's `evidence` field. The crate
file is never modified.

**Precedence in `build_evidence`:**
1. `aggregate_metrics` overrides (from a `--deep` walk) — highest.
2. The standard datasheet rollups already on the model
   (`evi:datasetCount`, `evi:totalEntities`, `evi:entitiesWithChecksums`,
   `evi:softwareCount`, `evi:schemaCount`, `evi:computationCount`) — used
   when present on a release root that wasn't scored with `--deep`.
3. The inline graph walk — correct for a single, fully-inlined crate.

Metrics supplied by `--deep` (keys on `aggregate_metrics` / fields echoed
in `evidence`): `dataset_count`, `software_count`, `schema_count`,
`computation_count`, `total_entities`, `good_computations` (software AND
I/O → 1.b), `computation_with_software` (1.b), `entities_with_provenance_link`
(5.d), `software_with_link` (1.c), `datasets_with_accession` (5.b),
`datasets_sourced` (1.a — derivedFrom / generatedBy / accession),
`distribution_link_count` + `distinct_protocols` (6.b — URLs live on
sub-crate datasets), `entities_with_hash` + `hashable_entities` (3.c),
`tabular_dataset_count` / `tabular_with_schema` / `tabular_with_stats`
(0.c, 2.b).

To add a new coverage metric: add the field to `AggregatedMetrics` and
`_accumulate_entity_metrics` (`fairscape-cli/.../models/rocrate.py`), map
it in `_deep_coverage_metrics` (`rocrate_commands.py`), consume it in
`aiready_extract.build_evidence` via the `overrides` dict, and echo it in
`AIReadyV2._evidence_dict`. No RO-Crate model change required.
