"""Probe-guidance support for autonomy loop-packet drafts."""

from __future__ import annotations

from typing import Any

try:
    from dev.scripts.coderabbit.probe_guidance import load_probe_guidance
except ModuleNotFoundError:  # broad-except: allow reason=devctl CLI runs from dev/scripts
    from coderabbit.probe_guidance import load_probe_guidance


def _backlog_items(payload: dict[str, Any]) -> list[dict]:
    rows = payload.get("backlog_items")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def load_loop_packet_probe_guidance(payload: dict[str, Any]) -> list[dict[str, object]]:
    """Load canonical probe guidance for the structured backlog slice."""
    items = _backlog_items(payload)
    if not items:
        return []
    return load_probe_guidance(items)
