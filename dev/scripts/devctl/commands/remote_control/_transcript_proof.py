"""Claude transcript proof helpers for remote-control lifecycle state."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path

from ...time_utils import parse_utc_timestamp

BUILTIN_REMOTE_CONTROL_ACTIVE_MARKER = "/remote-control is active"
REMOTE_CONTROL_SESSION_URL_RE = re.compile(
    r"https://claude\.ai/code/session_[A-Za-z0-9_-]+"
)


def read_jsonl_tail(path: Path, *, limit: int = 1000) -> list[Mapping[str, object]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    events: list[Mapping[str, object]] = []
    for line in lines[-limit:]:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            events.append(payload)
    return events


def latest_fresh_builtin_remote_control_proof(
    *,
    events: list[Mapping[str, object]],
    session_id: str,
    now_utc: str,
    max_age_seconds: int,
) -> Mapping[str, object] | None:
    now = parse_utc_timestamp(now_utc)
    if now is None:
        return None
    for index in range(len(events) - 1, -1, -1):
        raw = events[index]
        if not _is_builtin_remote_control_active(raw, session_id=session_id):
            continue
        timestamp = parse_utc_timestamp(raw.get("timestamp"))
        if timestamp is None or timestamp > now:
            continue
        if max((now - timestamp).total_seconds(), 0.0) > max_age_seconds:
            continue
        return raw
    return None


def latest_matching_builtin_remote_control_proof(
    *,
    events: list[Mapping[str, object]],
    session_id: str,
    before_event: Mapping[str, object],
    now_utc: str,
    max_age_seconds: int,
) -> Mapping[str, object] | None:
    """Find fresh built-in Claude remote-control proof in the same session."""
    now = parse_utc_timestamp(now_utc)
    before = parse_utc_timestamp(before_event.get("timestamp"))
    if now is None or before is None:
        return None
    for index in range(len(events) - 1, -1, -1):
        raw = events[index]
        if not _is_builtin_remote_control_active(raw, session_id=session_id):
            continue
        timestamp = parse_utc_timestamp(raw.get("timestamp"))
        if timestamp is None or timestamp > before or timestamp > now:
            continue
        if max((now - timestamp).total_seconds(), 0.0) > max_age_seconds:
            continue
        return raw
    return None


def remote_control_session_url(raw: Mapping[str, object]) -> str:
    for value in (_text(raw.get("url")), _text(raw.get("content"))):
        match = REMOTE_CONTROL_SESSION_URL_RE.search(value)
        if match:
            return match.group(0)
    return ""


def _is_builtin_remote_control_active(
    raw: Mapping[str, object],
    *,
    session_id: str,
) -> bool:
    return (
        _same_session(raw, session_id)
        and _text(raw.get("type")) == "system"
        and _text(raw.get("subtype")) == "bridge_status"
        and BUILTIN_REMOTE_CONTROL_ACTIVE_MARKER in _text(raw.get("content"))
        and bool(remote_control_session_url(raw))
    )


def _same_session(raw: Mapping[str, object], session_id: str) -> bool:
    raw_session_id = _text(raw.get("sessionId"))
    return not raw_session_id or raw_session_id == session_id


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "latest_fresh_builtin_remote_control_proof",
    "latest_matching_builtin_remote_control_proof",
    "read_jsonl_tail",
    "remote_control_session_url",
]
