"""JSONL persistence helpers for relaunch-loop state."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .jsonl_support import parse_json_line_dict
from .relaunch_loop_models import AgentRelaunchTrigger, SliceClosureEvent
from .state_store_authority import append_json_mapping


def append_jsonl(path: Path, payload: Mapping[str, object]) -> int:
    """Append one JSON object and return the byte offset used."""
    result = append_json_mapping(
        path,
        payload,
        store_id=path.name,
    )
    return result.byte_offset


def load_slice_closure_events(path: Path) -> tuple[SliceClosureEvent, ...]:
    """Load SliceClosureEvent rows from a JSONL trace."""
    events: list[SliceClosureEvent] = []
    for payload in _load_jsonl(path):
        event = SliceClosureEvent.from_mapping(payload)
        if event is not None:
            events.append(event)
    return tuple(events)


def load_relaunch_triggers(path: Path) -> tuple[AgentRelaunchTrigger, ...]:
    """Load AgentRelaunchTrigger rows from a JSONL queue."""
    triggers: list[AgentRelaunchTrigger] = []
    for payload in _load_jsonl(path):
        trigger = AgentRelaunchTrigger.from_mapping(payload)
        if trigger is not None:
            triggers.append(trigger)
    return tuple(triggers)


def pending_relaunch_triggers(path: Path) -> tuple[AgentRelaunchTrigger, ...]:
    """Load pending queue rows for a dispatcher tick."""
    return tuple(row for row in load_relaunch_triggers(path) if row.status == "pending")


def _load_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return ()
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(lines, start=1):
        payload = parse_json_line_dict(
            line,
            source=str(path),
            line_number=index,
            warning_sink=lambda _message: None,
        )
        if payload is not None:
            rows.append(payload)
    return tuple(rows)


__all__ = [
    "append_jsonl",
    "load_relaunch_triggers",
    "load_slice_closure_events",
    "pending_relaunch_triggers",
]
