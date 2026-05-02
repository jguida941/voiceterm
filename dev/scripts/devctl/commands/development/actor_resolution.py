"""Actor resolution for the typed `/develop` controller."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any


def resolve_actor(
    args: Any,
    review_state: Mapping[str, object],
) -> tuple[str, str]:
    """Resolve the actor lane without silently hardcoding a provider."""
    requested = str(getattr(args, "actor", "auto") or "auto").strip().lower()
    if requested and requested != "auto":
        return requested, "explicit_arg"

    env_actor = _environment_actor()
    if env_actor:
        return env_actor, "caller_environment"

    attention_actor = _single_pending_attention_actor(review_state)
    if attention_actor:
        return attention_actor, "packet_attention"

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


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


__all__ = ["resolve_actor"]
