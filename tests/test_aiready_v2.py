"""Tests for the v2 deterministic AI-Ready grader.

Per-rubric boundary tests drive the scorers with hand-built Evidence
snapshots (no pydantic friction); integration tests run the full
score_rocrate_v2 entry point over the real RO-Crate fixtures and assert
v2 is harsher than v1.
"""
import json
from pathlib import Path

import pytest

from fairscape_models.conversion.mapping import AIReadyV2 as v2
from fairscape_models.conversion.mapping.aiready_extract import Evidence
from fairscape_models.conversion.mapping.AIReadyV2 import score_rocrate_v2
from fairscape_models.conversion.mapping.AIReady import score_rocrate
from fairscape_models.conversion.models.AIReadyV2 import AIReadyScoreV2

FIXTURES = Path(__file__).parent / "test_rocrates"
FIXTURE_NAMES = ["release", "images", "LakeDB"]


def mk_ev(**kw) -> Evidence:
    """Evidence with sensible empty defaults; override only what a test needs."""
    base = dict(root={}, context_namespaces=[], recognized_standards=[])
    base.update(kw)
    return Evidence(**base)


# --- 1.b Traceable: the headline v2 improvement ---------------------------

def test_traceable_requires_io_and_software():
    # 10/10 good computations -> Substantive
    assert v2.score_traceable(mk_ev(computation_count=10, good_computations=10)).score == 2
    # computations exist but none are "good" -> Partial
    assert v2.score_traceable(mk_ev(computation_count=10, good_computations=0)).score == 1
    # half good (0.5 < 0.8) -> Partial
    assert v2.score_traceable(mk_ev(computation_count=10, good_computations=5)).score == 1
    # no computations at all -> Absent
    assert v2.score_traceable(mk_ev(computation_count=0, good_computations=0)).score == 0


# --- 5.d Associated: coverage, not "is there at least one" ----------------

def test_associated_is_coverage_based():
    assert v2.score_associated(mk_ev(total_entities=10, entities_with_provenance_link=9)).score == 2
    assert v2.score_associated(mk_ev(total_entities=10, entities_with_provenance_link=4)).score == 1
    assert v2.score_associated(mk_ev(total_entities=10, entities_with_provenance_link=1)).score == 0


def test_associated_penalizes_unlinked_subcrates():
    ev = mk_ev(total_entities=10, entities_with_provenance_link=9,
               sub_crate_count=2, sub_crates_linked=0)
    assert v2.score_associated(ev).score == 1  # high coverage but orphaned sub-crates


# --- 1.d Key Actors: OR became AND ----------------------------------------

def test_key_actors_needs_author_and_publisher_and_orcid():
    full = mk_ev(author_count=3, authors_with_orcid=2, has_publisher=True)
    assert v2.score_key_actors(full).score == 2
    # authors + publisher but no ORCIDs -> Partial
    assert v2.score_key_actors(mk_ev(author_count=3, authors_with_orcid=0, has_publisher=True)).score == 1
    # single plain author, no publisher -> Absent
    assert v2.score_key_actors(mk_ev(author_count=1, has_publisher=False)).score == 0


# --- 3.c Verifiable: hash coverage ----------------------------------------

def test_verifiable_hash_coverage():
    assert v2.score_verifiable(mk_ev(hashable_entities=10, entities_with_hash=10)).score == 2
    assert v2.score_verifiable(mk_ev(hashable_entities=10, entities_with_hash=5)).score == 1
    assert v2.score_verifiable(mk_ev(hashable_entities=10, entities_with_hash=0)).score == 0


# --- 0.a Findable: pid AND archive ----------------------------------------

def test_findable_needs_pid_and_archive():
    pid_and_archive = mk_ev(root={"identifier": "https://doi.org/10.1/x",
                                   "publisher": "Deposited in zenodo.org"})
    assert v2.score_findable(pid_and_archive).score == 2
    pid_only = mk_ev(root={"identifier": "https://doi.org/10.1/x"})
    assert v2.score_findable(pid_only).score == 1
    neither = mk_ev(root={"@id": "local-id-123"})
    assert v2.score_findable(neither).score == 0


# --- 0.d Reusable: resolvable license -------------------------------------

def test_reusable_license_resolvability():
    assert v2.score_reusable(mk_ev(root={"license": "https://creativecommons.org/licenses/by/4.0/"})).score == 2
    assert v2.score_reusable(mk_ev(root={"license": "see the README"})).score == 1
    assert v2.score_reusable(mk_ev(root={})).score == 0


# --- 2.e Data Quality: AND of two narratives ------------------------------

def test_data_quality_and():
    assert v2.score_data_quality(mk_ev(root={"rai:dataCollection": "x", "rai:dataCollectionMissingData": "y"})).score == 2
    assert v2.score_data_quality(mk_ev(root={"rai:dataCollection": "x"})).score == 1
    assert v2.score_data_quality(mk_ev(root={})).score == 0


# --- Integration over real fixtures ---------------------------------------

@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_score_rocrate_v2_on_fixtures(name):
    crate = json.loads((FIXTURES / name / "ro-crate-metadata.json").read_text())
    score = score_rocrate_v2(crate)
    assert isinstance(score, AIReadyScoreV2)
    assert 0 <= score.total_earned <= 56
    assert score.total_possible == 56
    assert len(score.criteria) == 7
    assert sum(len(c.rubrics) for c in score.criteria) == 28
    # every rubric in range
    for c in score.criteria:
        for r in c.rubrics:
            assert r.score in (0, 1, 2)
            assert r.label in ("Absent", "Partial", "Substantive")


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_v2_is_harsher_than_v1(name):
    crate = json.loads((FIXTURES / name / "ro-crate-metadata.json").read_text())
    v2_score = score_rocrate_v2(crate)
    v1_score = score_rocrate(crate)

    # v1 fraction = (# has_content True) / 28
    v1_true = 0
    for cat_name in ("fairness", "provenance", "characterization",
                     "pre_model_explainability", "ethics", "sustainability", "computability"):
        cat = getattr(v1_score, cat_name)
        for val in cat.__dict__.values():
            if getattr(val, "has_content", False):
                v1_true += 1
    v1_fraction = v1_true / 28
    v2_fraction = v2_score.total_earned / 56
    assert v2_fraction <= v1_fraction


def test_formerly_hardcoded_rubrics_can_drop():
    """v1 hard-coded 5.d, 6.c, 6.d (and others) to pass; v2 must be able to
    score them below 2 on a sparse crate."""
    crate = json.loads((FIXTURES / "LakeDB" / "ro-crate-metadata.json").read_text())
    score = score_rocrate_v2(crate)
    by_id = {r.id: r.score for c in score.criteria for r in c.rubrics}
    assert by_id["6.d"] < 2  # contextualized no longer a free pass
    assert min(by_id.values()) == 0  # at least one Absent on a sparse crate


# --- Threshold tunability --------------------------------------------------

def test_thresholds_are_tunable(monkeypatch):
    # A borderline 50%-coverage traceable scores Partial at the default 0.80
    ev = mk_ev(computation_count=10, good_computations=5)
    assert v2.score_traceable(ev).score == 1
    # Lowering the substantive bar below the coverage flips it to Substantive
    monkeypatch.setattr(v2, "T_SUBSTANTIVE", 0.5)
    assert v2.score_traceable(ev).score == 2
