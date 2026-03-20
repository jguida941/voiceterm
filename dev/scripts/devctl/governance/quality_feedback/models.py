"""Typed dataclasses and contract constants for governance quality feedback."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


QUALITY_FEEDBACK_CONTRACT_ID = "QualityFeedbackSnapshot"
QUALITY_FEEDBACK_SCHEMA_VERSION = 1

GRADE_THRESHOLDS: list[tuple[float, str]] = [
    (90.0, "A"),
    (80.0, "B"),
    (70.0, "C"),
    (60.0, "D"),
]
DEFAULT_GRADE = "F"


def letter_grade(score: float) -> str:
    """Map a 0-100 score to a letter grade."""
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return DEFAULT_GRADE


# -- Sub-score weights -------------------------------------------------------

SUB_SCORE_WEIGHTS: dict[str, float] = dict((
    ("halstead_mi", 0.20),
    ("code_shape", 0.10),
    ("duplication", 0.10),
    ("guard_issue_burden", 0.20),
    ("finding_density", 0.15),
    ("time_to_green", 0.10),
    ("cleanup_rate", 0.15),
))

# -- FP root cause categories ------------------------------------------------

FP_ROOT_CAUSES = frozenset(
    {"context_blind", "threshold_noise", "style_opinion", "pattern_mismatch", "unknown"}
)

# -- Dataclasses -------------------------------------------------------------


@dataclass(frozen=True)
class SubScoreEntry:
    """One sub-score component of the composite maintainability score."""

    name: str
    value: float
    weight: float
    weighted: float
    available: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LensScore:
    """One quality lens grouping related sub-scores."""

    lens: str
    score: float
    grade: str
    available: bool
    sub_scores: tuple[SubScoreEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "lens": self.lens,
            "score": self.score,
            "grade": self.grade,
            "available": self.available,
            "sub_scores": {e.name: e.to_dict() for e in self.sub_scores},
        }


# Lens definitions: which sub-scores belong to each lens.
LENS_MEMBERSHIP: dict[str, tuple[str, ...]] = {
    "code_health": ("halstead_mi", "code_shape", "duplication"),
    "governance_quality": ("guard_issue_burden", "finding_density", "cleanup_rate"),
    "operability": ("time_to_green",),
}


@dataclass(frozen=True)
class MaintainabilityResult:
    """Composite maintainability score with 3-lens breakdown."""

    overall: float
    grade: str
    sub_scores: tuple[SubScoreEntry, ...]
    lenses: tuple[LensScore, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "overall": self.overall,
            "grade": self.grade,
            "sub_scores": {entry.name: entry.to_dict() for entry in self.sub_scores},
        }
        if self.lenses:
            result["lenses"] = {lens.lens: lens.to_dict() for lens in self.lenses}
        return result


@dataclass(frozen=True)
class HalsteadFileMetrics:
    """Halstead metrics for a single source file."""

    path: str
    language: str
    loc: int
    n1: int  # distinct operators
    n2: int  # distinct operands
    big_n1: int  # total operators
    big_n2: int  # total operands
    vocabulary: int
    program_length: int
    volume: float
    difficulty: float
    effort: float
    estimated_bugs: float
    maintainability_index: float


@dataclass(frozen=True)
class HalsteadSummary:
    """Aggregate Halstead metrics across all scanned files."""

    files_scanned: int
    total_loc: int
    avg_volume: float
    avg_difficulty: float
    avg_effort: float
    avg_maintainability_index: float
    estimated_total_bugs: float
    by_language: dict[str, dict[str, float]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FPClassification:
    """One classified false-positive finding."""

    finding_id: str
    check_id: str
    file_path: str
    root_cause: str
    confidence: str  # "high", "medium", "low"
    evidence: str


@dataclass(frozen=True)
class FPAnalysis:
    """Aggregate false-positive analysis across all adjudicated findings."""

    total_fp_count: int
    by_root_cause: tuple[dict[str, Any], ...]
    classified_findings: tuple[FPClassification, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_fp_count": self.total_fp_count,
            "by_root_cause": list(self.by_root_cause),
            "classified_findings": [asdict(f) for f in self.classified_findings],
        }


@dataclass(frozen=True)
class CheckQualityScore:
    """Quality metrics for one guard or probe."""

    check_id: str
    signal_type: str
    total_findings: int
    true_positive_count: int
    false_positive_count: int
    precision_pct: float
    fp_rate_pct: float
    cleanup_rate_pct: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ImprovementDelta:
    """Change between two quality snapshots."""

    overall_score_delta: float
    previous_score: float | None
    current_score: float
    improved_checks: tuple[dict[str, Any], ...]
    degraded_checks: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score_delta": self.overall_score_delta,
            "previous_score": self.previous_score,
            "current_score": self.current_score,
            "improved_checks": list(self.improved_checks),
            "degraded_checks": list(self.degraded_checks),
        }


@dataclass(frozen=True)
class Recommendation:
    """One structured AI recommendation for governance tuning."""

    priority: int
    check_id: str
    category: str  # fp_reduction, threshold_tune, coverage_gap, cleanup_stall
    action: str
    evidence: str
    estimated_impact: str  # high, medium, low


@dataclass(frozen=True)
class QualityFeedbackSnapshot:
    """Top-level quality feedback report — the artifact contract payload."""

    schema_version: int
    contract_id: str
    command: str
    generated_at_utc: str
    repo_name: str
    maintainability: MaintainabilityResult
    halstead_summary: HalsteadSummary
    false_positive_analysis: FPAnalysis
    check_quality_scores: tuple[CheckQualityScore, ...]
    improvement_delta: ImprovementDelta | None
    recommendations: tuple[Recommendation, ...]

    def to_dict(self) -> dict[str, Any]:
        header: dict[str, Any] = {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "command": self.command,
            "generated_at_utc": self.generated_at_utc,
            "repo_name": self.repo_name,
        }
        scores: dict[str, Any] = {
            "maintainability_score": self.maintainability.to_dict(),
            "halstead_summary": self.halstead_summary.to_dict(),
            "false_positive_analysis": self.false_positive_analysis.to_dict(),
            "check_quality_scores": [s.to_dict() for s in self.check_quality_scores],
        }
        tail: dict[str, Any] = {
            "improvement_delta": (
                self.improvement_delta.to_dict() if self.improvement_delta else None
            ),
            "recommendations": [asdict(r) for r in self.recommendations],
        }
        return {**header, **scores, **tail}
