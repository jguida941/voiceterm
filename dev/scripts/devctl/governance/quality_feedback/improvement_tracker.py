"""Snapshot-to-snapshot delta computation for quality improvement tracking."""

from __future__ import annotations

from typing import Any

from .models import CheckQualityScore, ImprovementDelta


def compute_improvement_delta(
    *,
    current_score: float,
    current_check_scores: list[CheckQualityScore],
    previous_snapshot: dict[str, Any] | None,
) -> ImprovementDelta:
    """Compare current quality metrics against a previous snapshot.

    If no previous snapshot exists, the delta is simply the current score
    with no per-check improvements/degradations.
    """
    if previous_snapshot is None:
        return ImprovementDelta(
            overall_score_delta=0.0,
            previous_score=None,
            current_score=current_score,
            improved_checks=(),
            degraded_checks=(),
        )

    prev_score = float(
        (previous_snapshot.get("maintainability_score") or {}).get("overall", 0.0)
    )
    overall_delta = round(current_score - prev_score, 2)

    prev_check_map: dict[str, dict[str, Any]] = {}
    for entry in previous_snapshot.get("check_quality_scores") or []:
        if isinstance(entry, dict) and entry.get("check_id"):
            prev_key = _composite_key(
                entry["check_id"],
                str(entry.get("signal_type") or "unknown"),
            )
            prev_check_map[prev_key] = entry

    improved: list[dict[str, Any]] = []
    degraded: list[dict[str, Any]] = []

    for current in current_check_scores:
        current_key = _composite_key(current.check_id, current.signal_type)
        prev = prev_check_map.get(current_key)
        if prev is None:
            continue
        prev_precision = float(prev.get("precision_pct", 0.0))
        delta = round(current.precision_pct - prev_precision, 2)
        if delta > 0.5:
            improved.append({
                "check_id": current.check_id,
                "precision_delta": delta,
                "current_precision_pct": current.precision_pct,
                "previous_precision_pct": prev_precision,
            })
        elif delta < -0.5:
            degraded.append({
                "check_id": current.check_id,
                "precision_delta": delta,
                "current_precision_pct": current.precision_pct,
                "previous_precision_pct": prev_precision,
            })

    improved.sort(key=lambda x: -x["precision_delta"])
    degraded.sort(key=lambda x: x["precision_delta"])

    return ImprovementDelta(
        overall_score_delta=overall_delta,
        previous_score=prev_score,
        current_score=current_score,
        improved_checks=tuple(improved),
        degraded_checks=tuple(degraded),
    )


def _composite_key(check_id: str, signal_type: str) -> str:
    """Build a stable lookup key from (check_id, signal_type)."""
    return f"{check_id}|{signal_type}"
