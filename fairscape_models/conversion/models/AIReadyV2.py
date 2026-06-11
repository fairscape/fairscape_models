"""Pydantic models for the v2 deterministic AI-Ready score.

The v2 grader follows the AI-Ready paper's 7 criteria x 28 sub-criteria
structure and scores each sub-criterion 0 / 1 / 2 (Absent / Partial /
Substantive), for a maximum of 56 points. Unlike v1's binary
``has_content`` model, every rubric carries a deterministic rationale,
the concrete evidence facts that drove the score, and the gaps that
would raise it.
"""
from typing import Any, Dict, List
from pydantic import BaseModel, Field

##########################################################################
# --- AI-Readiness v2 Score Models ---------------------------------------
##########################################################################

SCORE_LABELS = {0: "Absent", 1: "Partial", 2: "Substantive"}


class RubricScoreV2(BaseModel):
    """Deterministic score for one of the 28 AI-Ready sub-criteria."""
    id: str = Field(description="Rubric id, e.g. '1.b'")
    criterion: str = Field(description="Parent criterion, e.g. 'Provenance'")
    sub_criterion: str = Field(description="Sub-criterion name, e.g. 'Traceable'")
    score: int = Field(ge=0, le=2, description="0=Absent, 1=Partial, 2=Substantive")
    label: str = Field(description="Human label for the score")
    rationale: str = Field(description="Which deterministic rule fired and why")
    evidence: List[str] = Field(default_factory=list, description="Concrete facts that justify the score")
    gaps: List[str] = Field(default_factory=list, description="What would raise the score; empty when score == 2")


class CriterionScoreV2(BaseModel):
    """One of the 7 top-level criteria, aggregating its rubrics."""
    criterion: str
    rubrics: List[RubricScoreV2] = Field(default_factory=list)
    earned: int = 0
    possible: int = 0
    percentage: float = 0.0


class AIReadyScoreV2(BaseModel):
    """Full deterministic AI-Ready v2 score for an RO-Crate."""
    name: str = "AI-Ready Score v2"
    schema_version: int = 2
    criteria: List[CriterionScoreV2] = Field(default_factory=list)
    total_earned: int = 0
    total_possible: int = 56
    percentage: float = 0.0
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="The coverage counts the score was computed from (entity counts, "
        "good-computation/provenance/hash coverage, etc.). Self-contained so the score "
        "document is auditable without re-walking the crate, and so release coverage "
        "metrics live here rather than on the RO-Crate itself.")
