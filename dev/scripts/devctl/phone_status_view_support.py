"""Shared helpers for `devctl phone-status` projections and markdown views."""

from __future__ import annotations

from typing import Any

from .text_utils import truncate_text as truncate_status_text


def section_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def terminal_trace_rows(payload: dict[str, Any]) -> list[str]:
    terminal = section_dict(payload, "terminal")
    trace = terminal.get("trace")
    if not isinstance(trace, list):
        return []
    rows: list[str] = []
    for row in trace:
        text = str(row).strip()
        if text:
            rows.append(text)
    return rows


def next_action_rows(payload: dict[str, Any]) -> list[str]:
    loop_payload = section_dict(payload, "loop")
    rows = loop_payload.get("next_actions")
    if not isinstance(rows, list):
        return []
    actions: list[str] = []
    for row in rows:
        text = str(row).strip()
        if text:
            actions.append(text)
    return actions


def render_ralph_section_lines(ralph: dict[str, Any]) -> list[str]:
    """Render Ralph guardrail status as markdown bullet lines."""
    if not isinstance(ralph, dict) or not ralph.get("available"):
        return ["- unavailable"]
    return [
        f"- phase: {ralph.get('phase')}",
        f"- attempt: {ralph.get('attempt')}/{ralph.get('max_attempts')}",
        f"- fix_rate: {ralph.get('fix_rate_pct')}%",
        (
            f"- findings: {ralph.get('fixed_count')} fixed / "
            f"{ralph.get('total_findings')} total | "
            f"{ralph.get('unresolved_count')} unresolved"
        ),
        f"- branch: {ralph.get('branch') or 'n/a'}",
        f"- last_run: {ralph.get('last_run') or 'n/a'}",
    ]


OPERATOR_ACTIONS: list[dict[str, str]] = [
    {
        "name": "dispatch-report-only",
        "kind": "write",
        "guard": "policy-gated",
        "command": "python3 dev/scripts/devctl.py controller-action --action dispatch-report-only --branch develop --dry-run --format md",
    },
    {
        "name": "pause-loop",
        "kind": "write",
        "guard": "policy-gated",
        "command": "python3 dev/scripts/devctl.py controller-action --action pause-loop --dry-run --format md",
    },
    {
        "name": "resume-loop",
        "kind": "write",
        "guard": "policy-gated",
        "command": "python3 dev/scripts/devctl.py controller-action --action resume-loop --dry-run --format md",
    },
    {
        "name": "controller-report",
        "kind": "read",
        "command": "python3 dev/scripts/devctl.py autonomy-report --format md",
    },
    {"name": "ralph-start", "kind": "write", "guard": "policy-gated", "command": "devctl ralph-control start"},
    {"name": "ralph-pause", "kind": "write", "guard": "policy-gated", "command": "devctl ralph-control pause"},
    {"name": "ralph-status", "kind": "read", "guard": "none", "command": "devctl ralph-status --format md"},
]
