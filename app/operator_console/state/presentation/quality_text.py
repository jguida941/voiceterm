"""Quality/CI text assembly for Operator Console analytics surfaces."""

from __future__ import annotations

from typing import Callable

from ..core.models import OperatorConsoleSnapshot
from ..snapshots.analytics_snapshot import RepoAnalyticsSnapshot
from ..watchdog_presenter import watchdog_topline_lines


def build_quality_text(
    snapshot: OperatorConsoleSnapshot,
    repo_analytics: RepoAnalyticsSnapshot | None,
    *,
    ratio_bar: Callable[[float, float], str],
) -> str:
    """Render the analytics quality section from repo-visible state."""
    lines = ["QUALITY & CI", ""]
    lines.append(
        f"- Warnings: {len(snapshot.warnings)} | Pending approvals: {len(snapshot.pending_approvals)}"
    )
    quality = snapshot.quality_backlog
    if quality is not None:
        lines.append(
            (
                "- Guard backlog: "
                f"{quality.guard_failures} failures | "
                f"critical={quality.critical_paths} high={quality.high_paths} "
                f"medium={quality.medium_paths} low={quality.low_paths}"
            )
        )
        if quality.top_priorities:
            lines.append("- Top hotspots:")
            for row in quality.top_priorities[:3]:
                lines.append(f"  - [{row.severity}] {row.path}")
        if quality.warning:
            lines.append(f"- Collector warning: {quality.warning}")
    if snapshot.watchdog_snapshot is not None:
        lines.extend(["", "WATCHDOG", ""])
        lines.extend(watchdog_topline_lines(snapshot.watchdog_snapshot))
    if repo_analytics is None:
        lines.append("- Repo quality collectors are unavailable in this view.")
        return "\n".join(lines)
    if repo_analytics.mutation_score_pct is None:
        lines.append(
            f"- Mutation: {repo_analytics.mutation_note or 'mutation score unavailable'}"
        )
    else:
        lines.append(
            "- Mutation score: "
            f"{repo_analytics.mutation_score_pct:.1f}% "
            f"{ratio_bar(repo_analytics.mutation_score_pct, 100.0)}"
        )
        if repo_analytics.mutation_age_hours is not None:
            lines.append(
                f"- Mutation age: {repo_analytics.mutation_age_hours:.1f}h since latest outcomes"
            )
    if repo_analytics.ci_runs_total is None:
        lines.append(f"- Recent CI: {repo_analytics.ci_note or 'CI data unavailable'}")
        return "\n".join(lines)
    success = repo_analytics.ci_success_runs
    failed = repo_analytics.ci_failed_runs
    pending = repo_analytics.ci_pending_runs
    total = max(repo_analytics.ci_runs_total, success + failed + pending, 1)
    lines.append(
        "- Recent CI: "
        f"{success} green / {failed} failing / {pending} pending "
        f"{ratio_bar(success, total)}"
    )
    if repo_analytics.ci_note:
        lines.append(f"- CI note: {repo_analytics.ci_note}")
    return "\n".join(lines)
