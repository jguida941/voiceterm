"""Operation-state reconciliation for commit-pipeline status."""

from __future__ import annotations

from typing import Any


def operation_reconcile_state(
    view: dict[str, Any],
    *,
    commit_sha: str,
    current_head: str,
    receipt_parent: str,
) -> str:
    """Summarize where the governed commit/push lifecycle actually landed."""
    if _latest_report_published_current_head(view):
        return (
            "published_post_push_green"
            if view.get("latest_push_report_post_push_green")
            else "published_remote_post_push_pending"
        )
    ahead = view.get("ahead_of_upstream_commits")
    behind = view.get("behind_upstream_commits")
    if view.get("upstream_ref") and ahead == 0 and behind == 0:
        return "remote_matches_current_head"
    if isinstance(ahead, int) and ahead > 0:
        if commit_sha and current_head == commit_sha:
            return "commit_landed_waiting_for_push"
        if commit_sha and receipt_parent == commit_sha:
            return "managed_receipt_landed_waiting_for_push"
        return "local_ahead_waiting_for_push"
    if commit_sha and current_head == commit_sha:
        return "commit_landed_at_head"
    if commit_sha and receipt_parent == commit_sha:
        return "managed_receipt_landed_at_head"
    if view.get("latest_push_report_exists"):
        return "latest_push_report_stale_or_non_publication"
    if view.get("pipeline_exists"):
        return f"pipeline_state:{view.get('state') or 'unknown'}"
    return "no_pipeline"


def _latest_report_published_current_head(view: dict[str, Any]) -> bool:
    return bool(
        view.get("latest_push_report_matches_current_head")
        and view.get("latest_push_report_published_remote")
    )
