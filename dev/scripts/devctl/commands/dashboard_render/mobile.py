"""Mobile-narrow dashboard renderers for remote-control sessions."""

from __future__ import annotations

from typing import Any


def is_remote_control_terminal(snapshot: dict[str, Any]) -> bool:
    """Return True when terminal output should use the phone-narrow shape."""
    control_plane = snapshot.get("control_plane") or {}
    if not isinstance(control_plane, dict):
        return False
    return str(control_plane.get("operator_interaction_mode") or "").strip() == (
        "remote_control"
    )


def render_mobile_narrow_terminal(snapshot: dict[str, Any]) -> str:
    """Plain terminal view for remote-control sessions."""
    repo = snapshot.get("repo", {})
    summary = snapshot.get("summary", {})
    control_plane = snapshot.get("control_plane") or {}
    health = snapshot.get("health", {})
    publication = snapshot.get("publication", {})

    lines = [
        "GOVERNANCE DASHBOARD",
        f"Mode: {control_plane.get('operator_interaction_mode', 'remote_control')}",
        f"State: {str(summary.get('overall_state', 'unknown')).upper()}",
        "Blocker: "
        f"{control_plane.get('top_blocker') or summary.get('primary_blocker', 'none')}",
        "Next: "
        f"{control_plane.get('next_action') or summary.get('next_command_hint', 'n/a')}",
        f"Command: {control_plane.get('next_command', 'n/a')}",
        f"Repo: {repo.get('name', 'unknown')}",
        f"Branch: {repo.get('branch', 'unknown')}",
        f"HEAD: {repo.get('head', 'unknown')}",
        f"Dirty: {repo.get('dirty_files', 0)} file(s), {repo.get('worktree', 'unknown')}",
        f"Push: {publication.get('effective', 'n/a')}",
        f"Review: {control_plane.get('reviewer_mode', 'n/a')}",
        f"Freshness: {control_plane.get('reviewer_freshness', 'n/a')}",
        f"Accepted: {control_plane.get('review_accepted', False)}",
        "Implementation blocked: "
        f"{control_plane.get('implementation_blocked', False)}",
        "Runtime: "
        f"{control_plane.get('attention_status', health.get('attention_status', 'n/a'))}",
        "Runtime detail: "
        f"{control_plane.get('attention_summary', health.get('attention_summary', 'n/a'))}",
        f"Pending actions: {control_plane.get('pending_action_requests', 0)}",
    ]
    return "\n".join(lines)
