"""Builds an :class:`AgentMindSlice` from parsed rollout events.

The parser in ``commands/rollout_tail`` already classifies each JSONL
line into a typed :class:`RolloutEvent`. Here we take the next layer:
filter that stream down to decision-relevant events, project each one
into an :class:`AgentMindEvent`, and stamp a slice-level header that
other agents and tools can poll.

Keeping this module narrow (pure transforms over already-typed input)
lets the command entry point stay small and lets the test suite feed
hand-built RolloutEvents without touching the filesystem.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ...runtime.agent_mind_slice import (
    AGENT_MIND_CONTRACT_ID,
    AGENT_MIND_SCHEMA_VERSION,
    AgentMindEvent,
    AgentMindSlice,
)
from ...runtime.rollout_event import RolloutEvent
from .peer_awareness import build_agent_mind_peer_awareness


@dataclass(frozen=True, slots=True)
class SliceRequest:
    """Typed grouping of slice-build inputs.

    Keeps ``build_slice`` under the parameter-count guard and lets future
    additions (e.g. provider-specific filters) extend the request shape
    without changing every call site.
    """

    agent_provider: str
    session_id: str
    session_path: Path
    since_cursor: str | None
    limit: int
    now_utc: str | None = None

# Event kinds we always want in an agent's mind stream. Anything outside
# this set is dropped unless it carries an escalation or error flag.
_DECISION_EVENT_KINDS: frozenset[str] = frozenset(
    {
        "response_item:reasoning",
        "response_item:function_call",
        "response_item:message",
        "event_msg:task_complete",
        "event_msg:agent_message",
    }
)

# Explicit ignore list for high-frequency low-signal chatter. Keeping this
# separate from _DECISION_EVENT_KINDS makes the filter reason easy to read:
# "keep decision kinds OR escalations OR errors, minus explicit noise".
_NOISE_EVENT_KINDS: frozenset[str] = frozenset(
    {
        "event_msg:token_count",
        "event_msg:exec_command_end",
    }
)

_SUMMARY_CHAR_LIMIT = 120


def build_slice(
    events: Iterable[RolloutEvent],
    request: "SliceRequest | None" = None,
    **kwargs: Any,
) -> AgentMindSlice:
    """Construct a typed :class:`AgentMindSlice` from raw rollout events.

    ``events`` should already be tailed from the source JSONL. The rest
    of the build inputs arrive as a :class:`SliceRequest` (or legacy
    keyword arguments, for test fixtures that predate the dataclass).
    This function drops low-signal chatter, applies the optional
    ``since_cursor`` filter, caps to ``limit``, and computes slice-level
    header fields (latest task_complete / escalation / error timestamps,
    last_cursor, generated_at_utc).
    """
    resolved = _coerce_request(request, kwargs)
    decision_events, cursors = _collect_decision_events(events, request=resolved)
    if resolved.limit > 0 and len(decision_events) > resolved.limit:
        decision_events = decision_events[-resolved.limit:]

    peer_awareness = build_agent_mind_peer_awareness(
        decision_events,
        agent_provider=resolved.agent_provider,
    )
    policy = peer_awareness.get("policy")
    return AgentMindSlice(
        schema_version=AGENT_MIND_SCHEMA_VERSION,
        contract_id=AGENT_MIND_CONTRACT_ID,
        agent_provider=resolved.agent_provider,
        session_id=resolved.session_id,
        session_path=str(resolved.session_path),
        generated_at_utc=resolved.now_utc or _utcnow_iso(),
        last_cursor=cursors["last_cursor"],
        events=tuple(decision_events),
        event_count=len(decision_events),
        latest_task_complete_at=cursors["latest_task_complete"],
        latest_escalation_at=cursors["latest_escalation"],
        latest_error_at=cursors["latest_error"],
        peer_awareness_policy=policy if isinstance(policy, dict) else {},
        peer_awareness=peer_awareness,
    )


def _coerce_request(
    request: "SliceRequest | None",
    kwargs: dict[str, Any],
) -> "SliceRequest":
    """Accept either a typed request or legacy keyword arguments."""
    if request is not None:
        if kwargs:
            raise TypeError("build_slice accepts request or kwargs, not both")
        return request
    return SliceRequest(**kwargs)


def _collect_decision_events(
    events: Iterable[RolloutEvent],
    *,
    request: "SliceRequest",
) -> tuple[list[AgentMindEvent], dict[str, str]]:
    """Walk ``events`` once, applying filters and collecting cursors."""
    decision_events: list[AgentMindEvent] = []
    cursors = {
        "last_cursor": "",
        "latest_task_complete": "",
        "latest_escalation": "",
        "latest_error": "",
    }
    for raw_event in events:
        if not _is_decision_event(raw_event):
            continue
        if request.since_cursor and _timestamp_leq(
            raw_event.timestamp, request.since_cursor
        ):
            continue
        mind_event = _project_event(raw_event)
        decision_events.append(mind_event)
        _advance_cursors(cursors, raw_event=raw_event, mind_event=mind_event)
    return decision_events, cursors


def _advance_cursors(
    cursors: dict[str, str],
    *,
    raw_event: RolloutEvent,
    mind_event: AgentMindEvent,
) -> None:
    """Update the latest-cursor hash in place for one event."""
    timestamp = raw_event.timestamp or ""
    if timestamp and timestamp > cursors["last_cursor"]:
        cursors["last_cursor"] = timestamp
    if (
        raw_event.event_type == "event_msg:task_complete"
        and timestamp > cursors["latest_task_complete"]
    ):
        cursors["latest_task_complete"] = timestamp
    if mind_event.is_escalation and timestamp > cursors["latest_escalation"]:
        cursors["latest_escalation"] = timestamp
    if mind_event.is_error and timestamp > cursors["latest_error"]:
        cursors["latest_error"] = timestamp


def _is_decision_event(event: RolloutEvent) -> bool:
    """Return True when ``event`` should be surfaced in an agent mind."""
    if event.event_type in _NOISE_EVENT_KINDS:
        # Noise still gets through if it carries an error/escalation
        # flag; that is a real decision signal even if the raw kind is
        # otherwise low-signal.
        return bool(event.is_escalation_request or event.is_error)
    if event.event_type in _DECISION_EVENT_KINDS:
        return True
    return bool(event.is_escalation_request or event.is_error)


def _project_event(event: RolloutEvent) -> AgentMindEvent:
    """Promote a :class:`RolloutEvent` to an :class:`AgentMindEvent`."""
    payload = event.raw_payload.get("payload") if isinstance(event.raw_payload, dict) else None
    if not isinstance(payload, dict):
        payload = {}
    tool_name, tool_command = _tool_fields(event, payload=payload)
    summary = _compose_summary(event, payload=payload)
    return AgentMindEvent(
        timestamp=event.timestamp or "",
        event_type=event.event_type or "",
        summary=summary,
        tool_name=tool_name,
        tool_command=tool_command,
        is_escalation=bool(event.is_escalation_request),
        is_error=bool(event.is_error),
        raw_event_kind=event.event_type or "",
    )


def _tool_fields(event: RolloutEvent, *, payload: dict[str, Any]) -> tuple[str, str]:
    """Extract tool name + command for function_call events."""
    if event.event_type != "response_item:function_call":
        return "", ""
    name = str(payload.get("name", "") or "").strip()
    arguments = payload.get("arguments")
    decoded = _decode_arguments(arguments)
    command = ""
    if isinstance(decoded, dict):
        command = str(decoded.get("cmd") or decoded.get("command") or "").strip()
    elif name == "apply_patch":
        command = _patch_target_summary(arguments)
    return name, command[:_SUMMARY_CHAR_LIMIT]


def _decode_arguments(arguments: Any) -> Any:
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            return json.loads(arguments)
        except json.JSONDecodeError:
            return None
    return None


def _patch_target_summary(arguments: Any) -> str:
    """Extract a compact target summary from an ``apply_patch`` payload."""
    if not isinstance(arguments, str) or not arguments.strip():
        return ""
    operations: list[str] = []
    for raw_line in arguments.splitlines():
        line = raw_line.strip()
        if line.startswith("*** Add File: "):
            operations.append(
                f"add {_compact_patch_path(line.removeprefix('*** Add File: ').strip())}"
            )
            continue
        if line.startswith("*** Delete File: "):
            operations.append(
                "delete "
                f"{_compact_patch_path(line.removeprefix('*** Delete File: ').strip())}"
            )
            continue
        if line.startswith("*** Update File: "):
            operations.append(
                "update "
                f"{_compact_patch_path(line.removeprefix('*** Update File: ').strip())}"
            )
            continue
        if line.startswith("*** Move to: ") and operations:
            destination = _compact_patch_path(
                line.removeprefix("*** Move to: ").strip()
            )
            current = operations[-1]
            if current.startswith("update "):
                source = current.removeprefix("update ").strip()
                operations[-1] = f"move {source} -> {destination}"
    if not operations:
        return ""
    return "; ".join(_dedupe_preserving_order(operations[:4]))


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _compact_patch_path(path: str) -> str:
    stripped = path.strip()
    parts = [segment for segment in stripped.split("/") if segment]
    if len(parts) <= 4:
        return stripped
    return "/".join(parts[-4:])


def _compose_summary(event: RolloutEvent, *, payload: dict[str, Any]) -> str:
    """Build a one-line summary for an AgentMindEvent.

    Renders each decision kind from its payload first (reasoning text,
    task_complete's last_agent_message, agent_message.message) so the
    mind stream shows real words instead of bare type labels like
    ``event_msg[task_complete]``. Falls back to the classifier's
    pre-computed ``event.summary`` only when the payload-specific
    renderer has nothing useful to show.
    """
    kind = event.event_type or ""
    payload_summary = _payload_summary(kind, payload)
    if payload_summary:
        return _truncate(payload_summary, _SUMMARY_CHAR_LIMIT)
    if event.summary:
        return _truncate(event.summary, _SUMMARY_CHAR_LIMIT)
    return kind or "event"


def _payload_summary(kind: str, payload: dict[str, Any]) -> str:
    """Render a payload-specific summary string, or empty if none applies."""
    if kind == "response_item:reasoning":
        summary_field = payload.get("summary")
        if isinstance(summary_field, list) and summary_field:
            first = summary_field[0]
            if isinstance(first, dict):
                text = first.get("text") or first.get("content") or ""
                if isinstance(text, str) and text:
                    return text
        content = payload.get("content")
        if isinstance(content, str) and content:
            return content
        # Codex reasoning payloads often carry encrypted_content with no
        # plaintext, so returning an honest label beats leaking the bare
        # event_type ("response_item") into the mind stream.
        if payload.get("encrypted_content"):
            return "reasoning (encrypted)"
        return "reasoning"
    if kind == "event_msg:task_complete":
        last = payload.get("last_agent_message")
        if isinstance(last, str) and last:
            return f"task_complete: {last}"
        return "task_complete"
    if kind == "event_msg:agent_message":
        message = payload.get("message")
        if isinstance(message, str) and message:
            return message
        return ""
    return ""


def _truncate(text: str, limit: int) -> str:
    """Collapse whitespace and cut to ``limit`` characters."""
    squashed = " ".join(text.split())
    if len(squashed) <= limit:
        return squashed
    return squashed[: limit - 1] + "\u2026"


def _timestamp_leq(candidate: str, cursor: str) -> bool:
    """Return True when ``candidate`` is at or before ``cursor``.

    Timestamps in rollout JSONL are ISO-8601 UTC strings with a ``Z``
    suffix, so lexical comparison is equivalent to chronological order
    without needing to parse. An empty candidate is treated as
    unknown and kept (better to show a malformed timestamp than to drop
    potentially live reasoning).
    """
    if not candidate:
        return False
    return candidate <= cursor


def _utcnow_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 ``Z`` string."""
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat().replace("+00:00", "Z")
