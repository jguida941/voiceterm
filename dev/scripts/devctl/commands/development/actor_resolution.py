"""Actor resolution for the typed `/develop` controller."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any

from ...runtime.review_packet_inbox import packet_inbox_from_review_state
from ...runtime.review_packet_inbox_liveness import is_live_pending

_NON_CONDUCTOR_ACTORS = {"operator", "system"}


def resolve_actor(
    args: Any,
    review_state: Mapping[str, object],
) -> tuple[str, str]:
    """Resolve the actor lane without silently hardcoding a provider."""
    requested = str(getattr(args, "actor", "auto") or "auto").strip().lower()
    if requested and requested != "auto":
        return requested, "explicit_arg"

    attention_actor = _single_pending_attention_actor(review_state)
    if attention_actor:
        return attention_actor, "packet_attention"

    env_actor = _environment_actor()
    if env_actor:
        return env_actor, "caller_environment"

    return "codex", "default_fallback"


def _environment_actor() -> str:
    for key in ("DEVCTL_CALLER_AGENT", "VOICE_TERM_CALLER_AGENT"):
        actor = str(os.environ.get(key, "") or "").strip().lower()
        if actor:
            return actor
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE"):
        return "claude"
    return ""


def _single_pending_attention_actor(review_state: Mapping[str, object]) -> str:
    packet_inbox_actor = _single_packet_inbox_attention_actor(review_state)
    if packet_inbox_actor:
        return packet_inbox_actor

    live_packet_actor = _single_live_pending_packet_actor(review_state)
    if live_packet_actor:
        return live_packet_actor

    agent_sync = _mapping(review_state.get("agent_sync"))
    agents = _mapping(agent_sync.get("agents"))
    pending: list[str] = []
    for actor, row in agents.items():
        if not isinstance(row, Mapping):
            continue
        if _sequence(row.get("pending_packets_to_me")):
            pending.append(str(actor).strip().lower())
    unique = tuple(actor for actor in dict.fromkeys(pending) if actor)
    return unique[0] if len(unique) == 1 else ""


def _single_packet_inbox_attention_actor(review_state: Mapping[str, object]) -> str:
    inbox = packet_inbox_from_review_state(review_state)
    if inbox is None:
        return ""
    pending = [
        str(record.agent).strip().lower()
        for record in inbox.agents
        if _record_has_live_actionable_attention(record)
    ]
    unique = tuple(actor for actor in dict.fromkeys(pending) if actor)
    return unique[0] if len(unique) == 1 else ""


def _record_has_live_actionable_attention(record: object) -> bool:
    return bool(
        _sequence(getattr(record, "pending_actionable_packet_ids", ()))
        or str(getattr(record, "current_instruction_packet_id", "") or "").strip()
        or str(getattr(record, "latest_finding_packet_id", "") or "").strip()
    )


def _single_live_pending_packet_actor(review_state: Mapping[str, object]) -> str:
    pending: list[str] = []
    for packet in _sequence(review_state.get("packets")):
        if not isinstance(packet, Mapping):
            continue
        if not is_live_pending(packet):
            continue
        actor = str(packet.get("to_agent") or "").strip().lower()
        if actor and actor not in _NON_CONDUCTOR_ACTORS:
            pending.append(actor)
    unique = tuple(actor for actor in dict.fromkeys(pending) if actor)
    return unique[0] if len(unique) == 1 else ""


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


__all__ = ["resolve_actor"]
