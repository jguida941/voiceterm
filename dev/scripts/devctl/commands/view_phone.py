"""Phone surface renderers for devctl view."""

from __future__ import annotations

import json
from typing import Any

from ..time_utils import utc_timestamp


def render_phone_summary(args) -> str:
    """Compact mobile-optimized view from the dashboard snapshot."""
    from .dashboard import build_snapshot
    from .dashboard_summary import _compile_summary

    snapshot = build_snapshot()
    summary = _compile_summary(snapshot)
    payload = _phone_payload(snapshot, summary)

    if args.format == "json":
        return json.dumps(payload, indent=2)
    return _phone_markdown(summary, snapshot)


def _phone_payload(snapshot: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    """Build a slim JSON payload for phone surface."""
    coordination = snapshot.get("coordination", {})
    return {
        "command": "view",
        "surface": "phone",
        "mode": "summary",
        "timestamp": utc_timestamp(),
        "overall_state": summary.get("overall_state", "unknown"),
        "primary_blocker": summary.get("primary_blocker", "none"),
        "next_actor": summary.get("next_actor", "unknown"),
        "next_command_hint": summary.get("next_command_hint", ""),
        "infra_label": summary.get("infra_label", ""),
        "one_line": summary.get("one_line", ""),
        "pending_actions": coordination.get("pending_action_count", 0),
        "reviewer_age": coordination.get("reviewer_age", "--"),
    }


def _phone_markdown(summary: dict[str, Any], snapshot: dict[str, Any]) -> str:
    """Render phone-optimized compact markdown."""
    state = summary.get("overall_state", "unknown")
    blocker = summary.get("primary_blocker", "none")
    actor = summary.get("next_actor", "unknown")
    hint = summary.get("next_command_hint", "")
    infra = summary.get("infra_label", "")
    coordination = snapshot.get("coordination", {})
    pending = coordination.get("pending_action_count", 0)
    reviewer_age = coordination.get("reviewer_age", "--")
    lines = [
        f"## {state.upper()}",
        f"Blocker: {blocker}",
        f"Next: {actor} -- {hint}",
        f"Infra: {infra}",
        f"Reviewer: {reviewer_age} | Pending: {pending}",
    ]
    return "\n".join(lines)
