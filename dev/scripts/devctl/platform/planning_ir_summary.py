"""Summary rendering helpers for planning-IR next-slice output."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..triage.findings_priority_models import RankedFinding


@dataclass(frozen=True, slots=True)
class SliceSummaryContext:
    """Bounded context needed to render one next-slice summary line."""

    active_target_path: str
    review_candidate_paths: frozenset[str]
    finding_count_by_file: Counter[str]
    blocked: bool
    hot_paths: Mapping[str, float]


def slice_summary(
    *,
    context: SliceSummaryContext,
    plan_path: str,
    top_files: tuple[str, ...],
    scored_paths: Sequence[tuple[float, str]],
    best_ranked_finding: RankedFinding | None,
) -> str:
    """Render the bounded one-line summary for a next-slice recommendation."""
    finding_count = sum(
        context.finding_count_by_file.get(file_path, 0)
        for _score, file_path in scored_paths
    )
    hot_count = sum(
        1 for _score, file_path in scored_paths if file_path in context.hot_paths
    )
    parts: list[str] = []
    if finding_count:
        parts.append(f"{finding_count} live finding(s)")
    if best_ranked_finding is not None:
        parts.append(
            f"priority finding #{best_ranked_finding.rank} [{best_ranked_finding.severity}]"
    )
    if hot_count:
        parts.append(f"{hot_count} hot path(s)")
    if context.active_target_path == plan_path:
        parts.append("matches active target")
    if context.review_candidate_paths.intersection(top_files):
        parts.append("includes review-candidate scope")
    if context.blocked:
        parts.append("blocked until single-writer posture returns")
    return "; ".join(parts) or "owned plan slice"
