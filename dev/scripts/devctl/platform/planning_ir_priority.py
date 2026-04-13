"""Priority-ranking helpers shared by planning-IR reduction."""

from __future__ import annotations

from collections.abc import Sequence

from ..triage.findings_priority_models import RankedFinding


def best_ranked_finding_for_paths(
    file_paths: Sequence[str],
    ranked_findings: Sequence[RankedFinding],
) -> RankedFinding | None:
    """Return the highest-priority finding attached to the given file set."""
    path_set = {str(path).strip() for path in file_paths if str(path).strip()}
    if not path_set:
        return None
    best: RankedFinding | None = None
    for finding in ranked_findings:
        refs = ranked_finding_paths(finding)
        if not path_set.intersection(refs):
            continue
        if best is None or (finding.rank, -finding.severity_rank, finding.qid) < (
            best.rank,
            -best.severity_rank,
            best.qid,
        ):
            best = finding
    return best


def ranked_finding_paths(finding: RankedFinding) -> tuple[str, ...]:
    """Return the bounded file refs that should count toward planning priority."""
    if finding.matched_file_refs:
        return finding.matched_file_refs
    if finding.file_refs:
        return finding.file_refs
    if finding.primary_file:
        return (finding.primary_file,)
    return ()


def priority_bonus(best_ranked_finding: RankedFinding | None) -> float:
    """Apply a bounded score bonus so ranked findings affect slice ordering."""
    if best_ranked_finding is None or best_ranked_finding.rank <= 0:
        return 0.0
    return float(max(0, 50 - best_ranked_finding.rank))
