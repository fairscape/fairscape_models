"""
ontology.py — verified ontology look-ups + value coercion for schema inference.

The lookup tables are LOADED FROM DATA, not hand-typed, so the codes can be
audited against their published source and grown without editing Python. The
CSVs ship as package data in `reference_tables/`:

    dicom_modality.csv        DICOM CID 29 "Acquisition Modality" — the closed
                              modality code set (PS3.16). `snomed_uri`/`radlex_uri`
                              are enrichment columns filled in by review.
    dicom_bodypart_snomed.csv DICOM PS3.16 Annex L — the standard correspondence
                              from the dirty `BodyPartExamined` (0018,0015) string
                              to a SNOMED CT Anatomic Region code. Parsed verbatim
                              from the spec; nothing invented.
    units_qudt.csv            UCUM code + QUDT unit URI, keyed on the native unit
                              string (hand-verified set).

A token that is NOT in these tables gets a null URL (never a guessed one) — the
raw string is passed through for the human `schema add-*` annotation step.
"""

import csv
from collections import namedtuple
try:
    # importlib.resources.files() is Python 3.9+
    from importlib.resources import files as _resource_files
except ImportError:
    # Python 3.8 falls back to the importlib_resources backport
    from importlib_resources import files as _resource_files

__all__ = [
    "UNIT_MAP",
    "MODALITY_MAP",
    "ModalityTerms",
    "BODYPART_MAP",
    "STD_12_LEADS",
    "LOINC_12LEAD",
    "unit_terms",
    "anatomy_terms",
    "as_num",
]


def _read_table(name):
    path = _resource_files("fairscape_models.schema") / "reference_tables" / name
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _blank_to_none(s):
    s = (s or "").strip()
    return s or None


# UCUM unit code + QUDT unit URI, keyed on the lower-cased native unit string.
UNIT_MAP = {
    row["raw_unit"].strip().lower(): (row["ucum_code"].strip(), _blank_to_none(row["qudt_uri"]))
    for row in _read_table("units_qudt.csv")
}

# DICOM modality code -> coding-system URI (DICOM DCM scheme; the canonical home
# of the modality code, filled for every row) + optional SNOMED/RadLex enrichment
# (blank -> None so it drops out under exclude_none).
ModalityTerms = namedtuple("ModalityTerms", ["dcm_system_uri", "snomed_uri", "radlex_uri"])
MODALITY_MAP = {
    row["modality_code"].strip(): ModalityTerms(
        _blank_to_none(row["dcm_system_uri"]),
        _blank_to_none(row["snomed_uri"]),
        _blank_to_none(row["radlex_uri"]),
    )
    for row in _read_table("dicom_modality.csv")
}

# DICOM BodyPartExamined defined term (upper-case) -> (code meaning, SNOMED URI).
# The URI is built from the Annex L SNOMED code; the meaning is the spec's label.
BODYPART_MAP = {
    row["body_part_examined"].strip().upper(): (
        row["code_meaning"].strip(),
        f"http://snomed.info/id/{row['snomed_code'].strip()}",
    )
    for row in _read_table("dicom_bodypart_snomed.csv")
}

# The 12 standard leads of a diagnostic ECG; if a signal record carries exactly
# these, we attach the verified LOINC 12-lead EKG panel code at record level.
STD_12_LEADS = {"I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6"}
LOINC_12LEAD = "https://loinc.org/34534-8/"


def unit_terms(raw):
    """(ucum_code, qudt_url) for a native unit token; passthrough + null URL if unknown."""
    if not raw:
        return None, None
    hit = UNIT_MAP.get(str(raw).strip().lower())
    return hit if hit else (str(raw).strip(), None)


def anatomy_terms(raw):
    """
    (anatomy_label, snomed_url) for a DICOM BodyPartExamined term via the Annex L
    crosswalk; passthrough label + null URL if the term is unknown. (None, None)
    for an empty/absent value — anatomy is then left for the human step.
    """
    if not raw:
        return None, None
    hit = BODYPART_MAP.get(str(raw).strip().upper())
    return hit if hit else (str(raw).strip(), None)


def as_num(x):
    """int if integral else float — keeps 100 not 100.0 in the JSON."""
    if x is None:
        return None
    f = float(x)
    return int(f) if f.is_integer() else f
