"""Peer-awareness projection for agent-mind slices."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ...runtime.agent_mind_slice import AgentMindEvent
from ...runtime.peer_awareness_policy import (
    AGENT_MESSAGE_EMIT_BOUNDARY,
    PEER_AWARENESS_OBSERVATION_CONTRACT_ID,
    agent_message_boundary_decision,
    default_peer_awareness_policy,
)

# Typed warning surfaced when no multi-provider topology is present in the
# typed CollaborationSessionState. Per AntiDumbass amendment, the previous
# implementation hardcoded codex<->claude reciprocal; this warning is the
# typed signal that no live peer topology has been resolved.
NO_LIVE_PEER_TOPOLOGY_WARNING = "no_live_peer_topology_in_collaboration_session"


def build_agent_mind_peer_awareness(
    events: Sequence[AgentMindEvent],
    *,
    agent_provider: str,
    repo_root: Path | None = None,
) -> dict[str, object]:
    """Return peer-awareness status inferred from one agent-mind event window."""
    work_class = _infer_work_class(events)
    live_peers = _default_peer_provider(agent_provider, repo_root=repo_root)
    peer_warnings: tuple[str, ...] = ()
    if not live_peers:
        peer_warnings = (NO_LIVE_PEER_TOPOLOGY_WARNING,)
    # ``peer_provider`` stays a single-string field for backwards compatibility
    # with PeerAwarenessPolicy.peer_provider; the full ``peer_providers`` tuple
    # surfaces the typed multi-provider topology when one is present.
    peer_provider = live_peers[0] if live_peers else ""
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
        "peer_providers": list(live_peers),
        "peer_topology_warnings": list(peer_warnings),
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


def _default_peer_provider(
    agent_provider: str,
    *,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    """Return the live peer providers from typed ``CollaborationSessionState``.

    Per AntiDumbass amendment (``delete_after_ingest.md`` lines 731-870):
    provider names are adapter identities, not topology authority. The peer
    provider for a given agent must come from typed session state, never from
    a hardcoded codex<->claude reciprocal.

    Returns a tuple of every live peer provider in the typed
    ``CollaborationSessionState.participants`` whose ``provider`` is not the
    given ``agent_provider``. Returns an empty tuple when no typed session is
    locatable; callers should surface the typed warning rather than fall back
    to a two-provider assumption.
    """
    self_provider = str(agent_provider or "").strip().lower()
    if repo_root is None:
        return ()
    try:
        from ...runtime.review_state_locator import (
            load_review_state_payload,
        )
        from ...runtime.review_state_parser import review_state_from_payload
    except ImportError:  # pragma: no cover - import fail-closed
        return ()
    try:
        payload = load_review_state_payload(repo_root)
    except (OSError, ValueError):  # pragma: no cover - loader fail-closed
        return ()
    if payload is None:
        return ()
    try:
        review_state = review_state_from_payload(payload)
    except (AttributeError, TypeError, ValueError, KeyError):  # pragma: no cover - parser fail-closed
        return ()
    collaboration = getattr(review_state, "collaboration", None)
    if collaboration is None:
        return ()
    peers: list[str] = []
    seen: set[str] = set()
    for participant in getattr(collaboration, "participants", ()) or ():
        if not getattr(participant, "live", False):
            continue
        provider = str(getattr(participant, "provider", "") or "").strip().lower()
        if not provider or provider == self_provider or provider in seen:
            continue
        seen.add(provider)
        peers.append(provider)
    return tuple(peers)


__all__ = ["build_agent_mind_peer_awareness", "NO_LIVE_PEER_TOPOLOGY_WARNING"]
