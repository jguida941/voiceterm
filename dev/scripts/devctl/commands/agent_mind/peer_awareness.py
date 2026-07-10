"""Peer-awareness projection for agent-mind slices."""

from __future__ import annotations

from collections.abc import Sequence

from ...runtime.agent_mind_slice import AgentMindEvent
from ...runtime.peer_awareness_policy import (
    AGENT_MESSAGE_EMIT_BOUNDARY,
    PEER_AWARENESS_OBSERVATION_CONTRACT_ID,
    agent_message_boundary_decision,
    default_peer_awareness_policy,
)


def build_agent_mind_peer_awareness(
    events: Sequence[AgentMindEvent],
    *,
    agent_provider: str,
) -> dict[str, object]:
    """Return peer-awareness status inferred from one agent-mind event window."""
    work_class = _infer_work_class(events)
    peer_provider = _default_peer_provider(agent_provider)
    policy = default_peer_awareness_policy(
        role="implementer",
        work_class=work_class,
        peer_provider=peer_provider,
    )
    latest_message = _latest_agent_message(events)
    latest_poll = _latest_peer_poll(events)
    decision = agent_message_boundary_decision(
        packets=(),
        actor=agent_provider,
        actor_role=policy.role,
        policy=policy,
        peer_provider=peer_provider,
        boundary_at_utc=latest_message.timestamp if latest_message else "",
        last_peer_poll_at_utc=latest_poll.timestamp if latest_poll else "",
        pending_packet_count=0,
    )
    due = decision.action == "poll_peer_state"
    reason = decision.reason if latest_message else "no_agent_message_boundary"
    return {
        "contract_id": PEER_AWARENESS_OBSERVATION_CONTRACT_ID,
        "schema_version": 1,
        "boundary": AGENT_MESSAGE_EMIT_BOUNDARY,
        "agent_provider": agent_provider,
        "peer_provider": peer_provider,
        "work_class": work_class,
        "due": due,
        "reason": reason,
        "last_agent_message_at_utc": latest_message.timestamp if latest_message else "",
        "last_peer_poll_at_utc": latest_poll.timestamp if latest_poll else "",
        "last_peer_poll_command": latest_poll.tool_command if latest_poll else "",
        "next_commands": list(decision.next_commands if due else ()),
        "policy": policy.to_dict(),
    }


def _latest_agent_message(
    events: Sequence[AgentMindEvent],
) -> AgentMindEvent | None:
    for event in reversed(events):
        if event.event_type in {"event_msg:agent_message", "response_item:message"}:
            return event
    return None


def _latest_peer_poll(
    events: Sequence[AgentMindEvent],
) -> AgentMindEvent | None:
    for event in reversed(events):
        if event.event_type != "response_item:function_call":
            continue
        command = event.tool_command
        if _is_peer_poll_command(command):
            return event
    return None


def _is_peer_poll_command(command: str) -> bool:
    normalized = " ".join(str(command or "").lower().split())
    if "agent-mind" in normalized and "--agent" in normalized:
        return True
    if "review-channel" not in normalized:
        return False
    return "--action inbox" in normalized or "--action show" in normalized


def _infer_work_class(events: Sequence[AgentMindEvent]) -> str:
    recent_text = " ".join(
        f"{event.summary} {event.tool_command}".lower()
        for event in events[-5:]
    )
    long_running_terms = (
        "still running",
        "elapsed=",
        "elapsed ",
        "push pipeline",
        "push-preflight",
        "preflight",
        "pytest",
        "test shard",
        "subprocess",
    )
    if any(term in recent_text for term in long_running_terms):
        return "long_running_subprocess"
    return "interactive_turn"


def _default_peer_provider(agent_provider: str) -> str:
    provider = str(agent_provider or "").strip().lower()
    if provider == "codex":
        return "claude"
    if provider == "claude":
        return "codex"
    return "codex"


__all__ = ["build_agent_mind_peer_awareness"]
