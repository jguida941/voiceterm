"""Repo analytics presentation helpers for the Operator Console."""

from __future__ import annotations

from ..snapshots.analytics_snapshot import RepoAnalyticsSnapshot


def _build_repo_text(repo_analytics: RepoAnalyticsSnapshot | None) -> str:
    lines = ["WORKING TREE & HOTSPOTS", ""]
    if repo_analytics is None:
        lines.append("- Repo analytics are unavailable in this view.")
        return "\n".join(lines)
    if repo_analytics.collection_note:
        lines.append(f"- Repo analytics note: {repo_analytics.collection_note}")
        return "\n".join(lines)

    lines.append(f"- Branch: {repo_analytics.branch or 'unknown'}")
    lines.append(
        "- Dirty files: "
        f"{repo_analytics.changed_files} total "
        f"(A{repo_analytics.added_files} "
        f"M{repo_analytics.modified_files} "
        f"D{repo_analytics.deleted_files} "
        f"R{repo_analytics.renamed_files} "
        f"?{repo_analytics.untracked_files} "
        f"U{repo_analytics.conflicted_files})"
    )
    change_mix_total = max(
        1,
        repo_analytics.added_files
        + repo_analytics.modified_files
        + repo_analytics.deleted_files
        + repo_analytics.untracked_files
        + repo_analytics.conflicted_files,
    )
    lines.append(
        "- Change mix: "
        + (
            f"A{_ratio_bar(repo_analytics.added_files, change_mix_total, width=4)} "
            f"M{_ratio_bar(repo_analytics.modified_files, change_mix_total, width=4)} "
            f"D{_ratio_bar(repo_analytics.deleted_files, change_mix_total, width=4)} "
            f"?{_ratio_bar(repo_analytics.untracked_files, change_mix_total, width=4)} "
            f"U{_ratio_bar(repo_analytics.conflicted_files, change_mix_total, width=4)}"
        )
    )
    lines.append(
        "- Governance touchpoints: "
        + (
            "MASTER_PLAN touched"
            if repo_analytics.master_plan_updated
            else "MASTER_PLAN unchanged"
        )
        + " | "
        + (
            "CHANGELOG touched"
            if repo_analytics.changelog_updated
            else "CHANGELOG unchanged"
        )
    )
    lines.append("- Hotspots:")
    if repo_analytics.top_paths:
        for path in repo_analytics.top_paths:
            lines.append(f"  - {path}")
    else:
        lines.append("  - none")
    return "\n".join(lines)


def _ratio_bar(value: float, total: float, width: int = 10) -> str:
    if total <= 0:
        return "[..........]"
    ratio = max(0.0, min(1.0, float(value) / float(total)))
    filled = int(round(ratio * width))
    return "[" + ("#" * filled) + ("." * max(0, width - filled)) + "]"
