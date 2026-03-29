"""Composite maintainability score using Halstead MI + governance metrics.

Score formula (weighted average of 7 sub-scores, each normalized [0, 100]).
Only dimensions whose evidence is actually loaded participate in the average;
unavailable dimensions are excluded so they cannot inflate the result with
default-perfect values.

    MaintainabilityScore =
        0.20 * halstead_mi_score      (normalized avg MI from Halstead analysis)
      + 0.10 * code_shape_score       (oversize file ratio)
      + 0.10 * duplication_score      (copy-paste debt)
      + 0.20 * guard_issue_burden_score    (open guard findings per guard check)
      + 0.15 * finding_density_score       (open findings per scanned file)
      + 0.10 * time_to_green_score    (avg seconds to green)
      + 0.15 * cleanup_rate_score     (fixed / positive findings)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import (
    LENS_MEMBERSHIP,
    LensScore,
    MaintainabilityResult,
    SUB_SCORE_WEIGHTS,
    SubScoreEntry,
    letter_grade,
)


def _clamp(low: float, high: float, value: float) -> float:
    return max(low, min(high, value))


@dataclass
class ScoreInputs:
    """Raw metrics fed into the composite score formula.

    Sub-scores whose evidence was never loaded are excluded from the
    weighted average so they cannot inflate the composite with
    default-perfect values.  Set the ``_available`` flag for each
    dimension only when real evidence is present.
    """

    # Halstead MI (already 0-100 from the MI formula)
    avg_halstead_mi: float = 0.0
    halstead_mi_available: bool = False

    # Code shape
    oversize_files: int = 0
    total_files: int = 1
    code_shape_available: bool = False

    # Duplication
    dup_pairs: int = 0
    functions_scanned: int = 1
    duplication_available: bool = False

    # Guard issue burden (open, unresolved guard findings from governance ledger)
    open_guard_findings: int = 0
    guard_count: int = 1
    guard_issue_burden_available: bool = False

    # Finding density (open, unresolved findings per repo source file)
    open_positive_findings: int = 0
    total_source_files: int = 1
    finding_density_available: bool = False

    # Time to green (seconds)
    avg_ttg_seconds: float = 0.0
    time_to_green_available: bool = False

    # Cleanup rate (already 0-100)
    cleanup_rate_pct: float = 0.0
    cleanup_rate_available: bool = False


def _halstead_mi_score(inputs: ScoreInputs) -> float:
    """Halstead MI is already normalized 0-100."""
    return _clamp(0.0, 100.0, inputs.avg_halstead_mi)


def _code_shape_score(inputs: ScoreInputs) -> float:
    total = max(1, inputs.total_files)
    ratio = inputs.oversize_files / total
    return 100.0 - _clamp(0.0, 100.0, ratio * 400.0)


def _duplication_score(inputs: ScoreInputs) -> float:
    total = max(1, inputs.functions_scanned)
    ratio = inputs.dup_pairs / total
    return 100.0 - _clamp(0.0, 100.0, ratio * 500.0)


def _guard_issue_burden_score(inputs: ScoreInputs) -> float:
    """Open guard findings per guard check — linear: 1 open/guard = score 0."""
    total = max(1, inputs.guard_count)
    ratio = inputs.open_guard_findings / total
    return 100.0 - _clamp(0.0, 100.0, ratio * 100.0)


def _finding_density_score(inputs: ScoreInputs) -> float:
    """Open findings per repo source file — 0.5 open/file = score 0."""
    total = max(1, inputs.total_source_files)
    ratio = inputs.open_positive_findings / total
    return 100.0 - _clamp(0.0, 100.0, ratio * 200.0)


def _time_to_green_score(inputs: ScoreInputs) -> float:
    # 10 minutes (600s) avg = score of 0
    return 100.0 - _clamp(0.0, 100.0, (inputs.avg_ttg_seconds / 600.0) * 100.0)


def _cleanup_rate_score(inputs: ScoreInputs) -> float:
    return _clamp(0.0, 100.0, inputs.cleanup_rate_pct)


_SUB_SCORE_FUNCTIONS: dict[str, Any] = dict((
    ("halstead_mi", _halstead_mi_score),
    ("code_shape", _code_shape_score),
    ("duplication", _duplication_score),
    ("guard_issue_burden", _guard_issue_burden_score),
    ("finding_density", _finding_density_score),
    ("time_to_green", _time_to_green_score),
    ("cleanup_rate", _cleanup_rate_score),
))

# Maps sub-score name to the ScoreInputs availability flag attribute.
_AVAILABILITY_FLAGS: dict[str, str] = dict((
    ("halstead_mi", "halstead_mi_available"),
    ("code_shape", "code_shape_available"),
    ("duplication", "duplication_available"),
    ("guard_issue_burden", "guard_issue_burden_available"),
    ("finding_density", "finding_density_available"),
    ("time_to_green", "time_to_green_available"),
    ("cleanup_rate", "cleanup_rate_available"),
))


def compute_maintainability_score(inputs: ScoreInputs) -> MaintainabilityResult:
    """Compute the composite maintainability score from raw metrics.

    Only dimensions whose evidence is actually loaded (``*_available=True``)
    participate in the weighted average.  Unavailable dimensions are still
    listed in the sub-score breakdown with ``value=0`` and ``weighted=0``
    so consumers can see what was skipped.
    """
    entries: list[SubScoreEntry] = []
    available_weight_sum = 0.0
    available_weighted_sum = 0.0

    for name, weight in SUB_SCORE_WEIGHTS.items():
        flag_attr = _AVAILABILITY_FLAGS.get(name, "")
        available = getattr(inputs, flag_attr, False) if flag_attr else False
        func = _SUB_SCORE_FUNCTIONS[name]
        value = round(func(inputs), 2) if available else 0.0
        weighted = round(value * weight, 2) if available else 0.0
        if available:
            available_weight_sum += weight
            available_weighted_sum += weighted
        entries.append(SubScoreEntry(
            name=name,
            value=value,
            weight=weight,
            weighted=weighted,
            available=available,
        ))

    # Renormalize so available dimensions fill the full 0-100 range.
    if available_weight_sum > 0:
        overall = round(available_weighted_sum / available_weight_sum * 1.0, 2)
    else:
        overall = 0.0

    # Build per-lens scores from the sub-score entries.
    entry_by_name = {e.name: e for e in entries}
    lenses = _build_lenses(entry_by_name)

    return MaintainabilityResult(
        overall=overall,
        grade=letter_grade(overall),
        sub_scores=tuple(entries),
        lenses=lenses,
    )


def _build_lenses(
    entry_by_name: dict[str, SubScoreEntry],
) -> tuple[LensScore, ...]:
    """Group sub-scores into quality lenses and compute per-lens averages."""
    result: list[LensScore] = []
    for lens_name, members in LENS_MEMBERSHIP.items():
        lens_entries = tuple(entry_by_name[m] for m in members if m in entry_by_name)
        available_entries = [e for e in lens_entries if e.available]
        if available_entries:
            lens_score = round(
                sum(e.value for e in available_entries) / len(available_entries), 2
            )
            lens_available = True
        else:
            lens_score = 0.0
            lens_available = False
        result.append(LensScore(
            lens=lens_name,
            score=lens_score,
            grade=letter_grade(lens_score) if lens_available else "n/a",
            available=lens_available,
            sub_scores=lens_entries,
        ))
    return tuple(result)
