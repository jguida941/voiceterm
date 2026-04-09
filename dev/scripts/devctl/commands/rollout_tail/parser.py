"""Per-line parser and classifier for rollout session JSONL traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...runtime.rollout_event import RolloutEvent
from .constants import PROVIDER_CLAUDE, PROVIDER_CODEX
from .discovery import session_id_from_path


def parse_rollout_file(
    path: Path,
    *,
    provider: str,
    limit: int,
) -> list[RolloutEvent]:
    """Parse ``limit`` most recent lines from a provider JSONL trace."""
    session_id = session_id_from_path(path, provider=provider)
    lines = _tail_lines(path, limit=limit)
    events: list[RolloutEvent] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            raw = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, dict):
            continue
        events.append(classify_event(raw, provider=provider, session_id=session_id))
    return events


def classify_event(
    raw: dict[str, Any],
    *,
    provider: str,
    session_id: str,
) -> RolloutEvent:
    """Promote one raw JSONL dict into a typed :class:`RolloutEvent`."""
    if provider == PROVIDER_CODEX:
        return _classify_codex(raw, session_id=session_id)
    if provider == PROVIDER_CLAUDE:
        return _classify_claude(raw, session_id=session_id)
    return RolloutEvent(
        timestamp=str(raw.get("timestamp", "")),
        provider=provider,
        session_id=session_id,
        event_type=str(raw.get("type", "unknown")),
        raw_payload=raw,
        summary=_first_nonempty(raw),
    )


def _classify_codex(raw: dict[str, Any], *, session_id: str) -> RolloutEvent:
    event_type = str(raw.get("type", "unknown"))
    payload = raw.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}
    payload_type = str(payload.get("type", ""))
    full_type = f"{event_type}:{payload_type}" if payload_type else event_type

    is_escalation = _codex_is_escalation(payload)
    is_error = _codex_is_error(event_type, payload)
    summary = _codex_summary(event_type, payload, is_escalation=is_escalation)

    return RolloutEvent(
        timestamp=str(raw.get("timestamp", "")),
        provider=PROVIDER_CODEX,
        session_id=session_id,
        event_type=full_type,
        raw_payload=raw,
        is_escalation_request=is_escalation,
        is_error=is_error,
        summary=summary,
    )


def _codex_is_escalation(payload: dict[str, Any]) -> bool:
    if payload.get("type") != "function_call":
        return False
    arguments = payload.get("arguments", "")
    if isinstance(arguments, str):
        return "require_escalated" in arguments
    if isinstance(arguments, dict):
        return arguments.get("sandbox_permissions") == "require_escalated"
    return False


def _codex_is_error(event_type: str, payload: dict[str, Any]) -> bool:
    if event_type == "error":
        return True
    if payload.get("type") == "error":
        return True
    for key in ("error", "error_message", "err"):
        if payload.get(key):
            return True
    return False


def _codex_summary(
    event_type: str,
    payload: dict[str, Any],
    *,
    is_escalation: bool,
) -> str:
    if is_escalation:
        justification = _argument_field(payload, "justification")
        cmd = _argument_field(payload, "cmd")
        if justification:
            return f"ESCALATION: {justification}"
        if cmd:
            return f"ESCALATION: {cmd}"
        return "ESCALATION: sandbox permissions require_escalated"
    if payload.get("type") == "function_call":
        name = payload.get("name", "?")
        cmd = _argument_field(payload, "cmd")
        if cmd:
            return f"tool_call[{name}]: {cmd[:140]}"
        return f"tool_call[{name}]"
    if payload.get("type") == "message":
        role = payload.get("role", "?")
        text = extract_message_text(payload)
        return f"message[{role}]: {text[:160]}" if text else f"message[{role}]"
    if event_type == "event_msg":
        return f"event_msg[{payload.get('type','?')}]"
    if event_type == "session_meta":
        return f"session_meta id={payload.get('id','?')}"
    return event_type


def _argument_field(payload: dict[str, Any], key: str) -> str:
    """Extract a single field from a function_call arguments bag."""
    decoded = _decode_arguments(payload.get("arguments"))
    if isinstance(decoded, dict):
        return str(decoded.get(key, "")).strip()
    return ""


def _decode_arguments(args: Any) -> Any:
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return None
    return None


def extract_message_text(payload: dict[str, Any]) -> str:
    """Flatten a message payload's content array into a single string."""
    content = payload.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for entry in content:
            if isinstance(entry, dict):
                text = entry.get("text") or entry.get("content") or ""
                if isinstance(text, str) and text:
                    parts.append(text)
        return " ".join(parts)
    return ""


def _classify_claude(raw: dict[str, Any], *, session_id: str) -> RolloutEvent:
    event_type = str(raw.get("type", "unknown"))
    is_error = event_type == "error" or bool(raw.get("isError"))
    summary = _claude_summary(raw)
    return RolloutEvent(
        timestamp=str(raw.get("timestamp", "")),
        provider=PROVIDER_CLAUDE,
        session_id=session_id,
        event_type=event_type,
        raw_payload=raw,
        is_escalation_request=False,
        is_error=is_error,
        summary=summary,
    )


def _claude_summary(raw: dict[str, Any]) -> str:
    event_type = str(raw.get("type", "unknown"))
    if event_type in {"user", "assistant"}:
        message = raw.get("message") or {}
        if isinstance(message, dict):
            text = extract_message_text(message)
            if text:
                return f"{event_type}: {text[:160]}"
        return event_type
    if event_type == "system":
        subtype = raw.get("subtype") or raw.get("name") or ""
        return f"system[{subtype}]" if subtype else "system"
    return event_type


def _first_nonempty(raw: dict[str, Any]) -> str:
    for key in ("summary", "message", "text"):
        value = raw.get(key)
        if isinstance(value, str) and value:
            return value[:160]
    return str(raw.get("type", "unknown"))


def _tail_lines(path: Path, *, limit: int) -> list[str]:
    """Read ``limit`` tail lines from a file without buffering the whole file."""
    if limit <= 0:
        return []
    try:
        with path.open("rb") as handle:
            handle.seek(0, 2)
            file_size = handle.tell()
            block_size = 64 * 1024
            data = b""
            position = file_size
            while position > 0 and data.count(b"\n") <= limit:
                read_size = min(block_size, position)
                position -= read_size
                handle.seek(position)
                data = handle.read(read_size) + data
    except OSError:
        return []
    lines = data.splitlines()
    return [line.decode("utf-8", errors="replace") for line in lines[-limit:]]
