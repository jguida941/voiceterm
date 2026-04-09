"""Render helpers for the ``rollout-tail`` command.

Provides the terminal, json, and markdown surfaces consumed by the
command entrypoint. Renderers are deliberately pure functions so the
test suite can feed them hand-built :class:`RolloutEvent` instances
without going through the parser or file discovery paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ...runtime.rollout_event import RolloutEvent


def render_terminal(
    events: Iterable[RolloutEvent],
    *,
    source: Path | None,
) -> str:
    """Compact one-line-per-event table used by the default --format."""
    events_list = list(events)
    header = f"rollout-tail source={source}" if source else "rollout-tail source=<none>"
    lines = [header, "-" * min(80, max(20, len(header)))]
    if not events_list:
        lines.append("(no events)")
        return "\n".join(lines)
    for event in events_list:
        kind = _kind_label(event)
        timestamp = event.timestamp or "-"
        summary = event.summary or event.event_type
        lines.append(f"{timestamp} | {kind:12s} | {summary}")
    return "\n".join(lines)


def render_json(
    events: Iterable[RolloutEvent],
    *,
    source: Path | None,
) -> str:
    """Structured JSON payload for downstream tooling and tests."""
    payload = {
        "command": "rollout-tail",
        "source": str(source) if source else "",
        "events": [event.to_dict() for event in events],
    }
    return json.dumps(payload, indent=2)


def render_markdown(
    events: Iterable[RolloutEvent],
    *,
    source: Path | None,
) -> str:
    """Markdown variant suitable for bridge projection or chat pasting."""
    events_list = list(events)
    lines = ["# rollout-tail", ""]
    lines.append(f"- source: `{source}`" if source else "- source: (none)")
    lines.append(f"- event count: {len(events_list)}")
    lines.append("")
    if not events_list:
        lines.append("_no events_")
        return "\n".join(lines)
    for event in events_list:
        lines.extend(_markdown_event_block(event))
    return "\n".join(lines)


def _markdown_event_block(event: RolloutEvent) -> list[str]:
    block = [
        f"## {event.timestamp or '-'} [{_kind_label(event)}]",
        "",
        f"- event_type: `{event.event_type}`",
        f"- provider: {event.provider}",
        f"- session_id: `{event.session_id}`",
    ]
    if event.summary:
        block.append(f"- summary: {event.summary}")
    if event.is_escalation_request:
        block.append("- **BLOCKER**: sandbox escalation request")
    if event.is_error:
        block.append("- **ERROR**")
    block.append("")
    return block


def _kind_label(event: RolloutEvent) -> str:
    if event.is_escalation_request:
        return "ESCALATION"
    if event.is_error:
        return "ERROR"
    return "event"
