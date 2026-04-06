"""Renderers for the DashboardSnapshot: terminal (ANSI), markdown, JSON.

Section-specific renderers live in focused submodules:
- ``dashboard_render_helpers``: ANSI constants and formatting utilities
- ``dashboard_render_terminal``: dense multi-column ANSI terminal output
  (renders ``top_blocker`` and other ControlPlaneReadModel fields)
- ``dashboard_render_markdown``: plain markdown output
  (renders ``top_blocker`` and other ControlPlaneReadModel fields)
- ``dashboard_render_attention``: attention, doctor, and flow renderers

The ``top_blocker`` field from ``ControlPlaneReadModel`` is surfaced
through the terminal and markdown submodules. This module routes both
render paths through the dispatcher below.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from ..dashboard import _VIEW_SECTIONS
from . import attention as _attn
from . import terminal as _term
from . import markdown as _md
from .helpers import (
    _BOLD,
    _CYAN,
    _DIM,
    _GREEN,
    _RED,
    _RESET,
    _WIDTH,
    _YELLOW,
    _JOB_STATE_COLORS,
    _fmt_pct,
    _fmt_timer,
    _gate_color,
    _loop_label,
    _mode_display,
)

# Pre-compiled pattern for stripping ANSI escape sequences
_ANSI_RE = re.compile(r"\033\[[^m]*m")


def render_json(snapshot: dict[str, Any]) -> str:
    """Raw DashboardSnapshot as formatted JSON."""
    return json.dumps(snapshot, indent=2)


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from *text* for non-terminal output."""
    return _ANSI_RE.sub("", text)


def _should_strip_color(no_color: bool) -> bool:
    """Return True when ANSI codes should be stripped.

    Respects the ``--no-color`` CLI flag and the ``NO_COLOR`` environment
    variable (see https://no-color.org/).
    """
    if no_color:
        return True
    return os.environ.get("NO_COLOR", "") != ""


def _view_includes(snapshot: dict[str, Any], section: str) -> bool:
    """Return True when the snapshot's view includes the given section.

    Overview (the default) includes everything.  Other views only render
    sections listed in ``_VIEW_SECTIONS``.  The ``summary`` and ``repo``
    sections are always included.
    """
    view = snapshot.get("view", "overview")
    allowed = _VIEW_SECTIONS.get(view, frozenset())
    if not allowed:
        return True  # overview -- render everything
    return section in allowed


def render_terminal(snapshot: dict[str, Any], *, no_color: bool = False) -> str:
    """ANSI-colored dense multi-column terminal dashboard output.

    When *no_color* is ``True`` (or the ``NO_COLOR`` env var is set),
    all ANSI escape sequences are stripped from the result so the output
    is safe for environments that do not interpret them.
    """
    lines: list[str] = []
    _term._render_summary_terminal(snapshot, lines)
    _term._render_header_terminal(snapshot, lines)
    if _view_includes(snapshot, "now"):
        _term._render_now_terminal(snapshot, lines)
    if _view_includes(snapshot, "reviewer_activity"):
        _term._render_reviewer_activity_terminal(snapshot, lines)
    if _view_includes(snapshot, "health"):
        _term._render_health_terminal(snapshot, lines)
    _attn.render_typed_attention_terminal(snapshot, lines)
    if _view_includes(snapshot, "workers"):
        _term._render_workers_terminal(snapshot, lines)
    if _view_includes(snapshot, "plan"):
        _term._render_plan_terminal(snapshot, lines)
    if _view_includes(snapshot, "findings"):
        _term._render_findings_terminal(snapshot, lines)
    if _view_includes(snapshot, "publication"):
        _term._render_publication_terminal(snapshot, lines)
    if _view_includes(snapshot, "quality"):
        _term._render_quality_terminal(snapshot, lines)
    if _view_includes(snapshot, "audit"):
        _term._render_audit_terminal(snapshot, lines)
    if _view_includes(snapshot, "analytics"):
        _term._render_analytics_terminal(snapshot, lines)
    if _view_includes(snapshot, "coordination"):
        _term._render_coordination_terminal(snapshot, lines)
    if _view_includes(snapshot, "flow"):
        _attn.render_flow_terminal(snapshot, lines)
    if _view_includes(snapshot, "timeline"):
        _term._render_timeline_terminal(snapshot, lines)
    result = "\n".join(lines)
    if _should_strip_color(no_color):
        result = strip_ansi(result)
    return result


def render_markdown(snapshot: dict[str, Any]) -> str:
    """Markdown-formatted dashboard output."""
    lines: list[str] = []
    _md._render_summary_markdown(snapshot, lines)
    _md._render_header_markdown(snapshot, lines)
    if _view_includes(snapshot, "now"):
        _md._render_now_markdown(snapshot, lines)
    if _view_includes(snapshot, "reviewer_activity"):
        _md._render_reviewer_activity_markdown(snapshot, lines)
    if _view_includes(snapshot, "health"):
        _md._render_health_markdown(snapshot, lines)
    _attn.render_typed_attention_markdown(snapshot, lines)
    if _view_includes(snapshot, "workers"):
        _md._render_workers_markdown(snapshot, lines)
    if _view_includes(snapshot, "plan"):
        _md._render_plan_markdown(snapshot, lines)
    if _view_includes(snapshot, "findings"):
        _md._render_findings_markdown(snapshot, lines)
    if _view_includes(snapshot, "publication"):
        _md._render_publication_markdown(snapshot, lines)
    if _view_includes(snapshot, "quality"):
        _md._render_quality_markdown(snapshot, lines)
    if _view_includes(snapshot, "audit"):
        _md._render_audit_markdown(snapshot, lines)
    if _view_includes(snapshot, "analytics"):
        _md._render_analytics_markdown(snapshot, lines)
    if _view_includes(snapshot, "coordination"):
        _md._render_coordination_markdown(snapshot, lines)
    if _view_includes(snapshot, "flow"):
        _attn.render_flow_markdown(snapshot, lines)
    if _view_includes(snapshot, "timeline"):
        _md._render_timeline_markdown(snapshot, lines)
    return "\n".join(lines)
