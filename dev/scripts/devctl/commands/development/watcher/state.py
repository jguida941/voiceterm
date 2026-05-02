"""Stored watcher state readers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path


def load_state(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def watcher_status(
    state: Mapping[str, object],
    *,
    runtime_idle_seconds: int | None,
    stale_seconds: int,
    stale_after_seconds: int,
) -> str:
    if (
        runtime_idle_seconds is not None
        and runtime_idle_seconds <= stale_after_seconds
    ):
        return "live"
    if not state:
        return "missing"
    if _text(state.get("stop_reason")):
        return "stopped"
    if stale_seconds > stale_after_seconds:
        return "stale"
    return "live"


def state_text(value: object) -> str:
    return _text(value)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["load_state", "state_text", "watcher_status"]
