"""Shared constants and utility functions for dashboard renderers.

Provides ANSI escape constants, job-state color mapping, and small
formatting helpers consumed by the terminal, markdown, and attention
render modules.
"""

from __future__ import annotations

from typing import Any

# ANSI escape helpers -- semantic colors only
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

# Job/review state color lookup built from grouped tuples
_JOB_STATE_COLORS: dict[str, str] = {}
for _color, _states in (
    (_CYAN, ("implementing", "active", "running")),
    (_YELLOW, ("review_needed", "stale", "waiting")),
    (_GREEN, ("idle", "pass", "done")),
    (_RED, ("blocked", "failed", "error", "fail")),
):
    for _s in _states:
        _JOB_STATE_COLORS[_s] = _color

# Dashboard total width for right-alignment
_WIDTH = 72


def _loop_label(mode: str) -> str:
    """Translate reviewer mode to a loop activity label."""
    if mode == "active_dual_agent":
        return "ACTIVE"
    if mode in ("single_agent", "tools_only"):
        return "INACTIVE"
    if mode in ("paused", "offline"):
        return "PAUSED"
    return "UNKNOWN"


def _mode_display(mode: str) -> str:
    """Human-readable mode label."""
    mapping = {
        "active_dual_agent": "Dual-agent",
        "single_agent": "Single-agent",
        "tools_only": "Tools-only",
        "paused": "Paused",
        "offline": "Offline",
    }
    return mapping.get(mode, mode)


def _gate_color(val: str) -> str:
    """Pick ANSI color for a quality gate value."""
    upper = val.upper()
    if upper == "PASS":
        return _GREEN
    if upper == "FAIL":
        return _RED
    return _DIM


def _fmt_timer(val: Any) -> str:
    """Format a duration value as '71.1s' or 'pending' for display."""
    if val is None or val == "n/a":
        return "pending"
    if isinstance(val, (int, float)):
        return f"{val:.1f}s"
    return str(val)


def _fmt_pct(val: Any) -> str:
    """Format a percentage value as '56.2%' or 'n/a' for display."""
    if val is None or val == "n/a":
        return "n/a"
    if isinstance(val, (int, float)):
        return f"{val}%"
    return str(val)


def _append_markdown_agent_counts(
    lines: list[str],
    agent_counts: dict[str, Any],
) -> None:
    """Append markdown health lines for live agent/runtime counts."""
    lines.append(
        "- **Active agents**: "
        f"{agent_counts.get('live_participants_total', 0)} live "
        f"({agent_counts.get('live_reviewer_total', 0)} reviewer, "
        f"{agent_counts.get('live_implementer_total', 0)} implementer)"
    )
    lines.append(
        "- **Planned lanes / worker budget**: "
        f"{agent_counts.get('planned_lane_total', 0)} / "
        f"{agent_counts.get('requested_worker_budget_total', 0)}"
    )
