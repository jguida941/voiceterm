"""Peer-awareness cadence and agent-message boundary checks."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

from .peer_awareness_clock import long_running_cadence, peer_poll_due
from .peer_awareness_packets import blocking_body_packet
from .session_route_scope import normalize_route_role
from .session_termination_body import (
    packet_body_show_command,
)

PEER_AWARENESS_POLICY_CONTRACT_ID = "PeerAwarenessPolicy"
PEER_AWARENESS_POLICY_SCHEMA_VERSION = 1
PEER_AWARENESS_DECISION_CONTRACT_ID = "PeerAwarenessDecision"
PEER_AWARENESS_OBSERVATION_CONTRACT_ID = "PeerAwarenessObservation"

AGENT_MESSAGE_EMIT_BOUNDARY = "agent_message_emit"
SUBPROCESS_HEARTBEAT_BOUNDARY = "subprocess_heartbeat"
TASK_BOUNDARY = "task_boundary"

REVIEW_CHANNEL_INBOX_OBSERVATION = "review_channel_inbox"
PEER_AGENT_MIND_OBSERVATION = "peer_agent_mind"
PACKET_BODY_OBSERVATION = "packet_body_observation"

_LONG_RUNNING_WORK_CLASSES = frozenset(
    {
        "long_running_subprocess",
        "push_pipeline",
        "test_shard",
    }
)


@dataclass(frozen=True, slots=True)
class PeerAwarenessPolicy:
    """Required peer-poll cadence for one role and work class."""

    role: str = "implementer"
    work_class: str = "interactive_turn"
    peer_provider: str = ""
    digest_sidecar_enabled: bool = False
    digest_sidecar_provider: str = ""
    cadence_seconds: int = 900
    boundary_events: tuple[str, ...] = (TASK_BOUNDARY,)
    required_observations: tuple[str, ...] = (
        REVIEW_CHANNEL_INBOX_OBSERVATION,
        PEER_AGENT_MIND_OBSERVATION,
    )
    contract_id: str = PEER_AWARENESS_POLICY_CONTRACT_ID
    schema_version: int = PEER_AWARENESS_POLICY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["boundary_events"] = list(self.boundary_events)
        payload["required_observations"] = list(self.required_observations)
        return payload


@dataclass(frozen=True, slots=True)
class PeerAwarenessDecision:
    """Boundary decision produced before an agent emits another progress message."""

    action: str
    reason: str
    boundary: str = AGENT_MESSAGE_EMIT_BOUNDARY
    peer_provider: str = ""
    cadence_seconds: int = 0
    poll_due: bool = False
    body_open_required: bool = False
    sidecar_required: bool = False
    blocking_packet_id: str = ""
    sidecar_provider: str = ""
    next_commands: tuple[str, ...] = ()
    contract_id: str = PEER_AWARENESS_DECISION_CONTRACT_ID
    schema_version: int = PEER_AWARENESS_POLICY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["next_commands"] = list(self.next_commands)
        return payload


def default_peer_awareness_policy(
    *,
    role: str,
    work_class: str = "interactive_turn",
    peer_provider: str = "",
    digest_sidecar_enabled: bool = False,
    digest_sidecar_provider: str = "",
) -> PeerAwarenessPolicy:
    """Return the repo-default peer-awareness policy for role/work class."""
    normalized_role = normalize_route_role(role) or "implementer"
    normalized_work_class = _text(work_class) or "interactive_turn"
    sidecar_provider = _text(digest_sidecar_provider) or _text(peer_provider)
    if normalized_work_class in _LONG_RUNNING_WORK_CLASSES:
        return PeerAwarenessPolicy(
            role=normalized_role,
            work_class=normalized_work_class,
            peer_provider=_text(peer_provider),
            digest_sidecar_enabled=bool(digest_sidecar_enabled),
            digest_sidecar_provider=sidecar_provider,
            cadence_seconds=long_running_cadence(normalized_role),
            boundary_events=(AGENT_MESSAGE_EMIT_BOUNDARY, SUBPROCESS_HEARTBEAT_BOUNDARY),
            required_observations=(
                REVIEW_CHANNEL_INBOX_OBSERVATION,
                PEER_AGENT_MIND_OBSERVATION,
                PACKET_BODY_OBSERVATION,
            ),
        )
    if normalized_role in {"dashboard", "observer", "reviewer"}:
        return PeerAwarenessPolicy(
            role=normalized_role,
            work_class=normalized_work_class,
            peer_provider=_text(peer_provider),
            digest_sidecar_enabled=bool(digest_sidecar_enabled),
            digest_sidecar_provider=sidecar_provider,
            cadence_seconds=300,
            boundary_events=(TASK_BOUNDARY, AGENT_MESSAGE_EMIT_BOUNDARY),
        )
    return PeerAwarenessPolicy(
        role=normalized_role,
        work_class=normalized_work_class,
        peer_provider=_text(peer_provider),
        digest_sidecar_enabled=bool(digest_sidecar_enabled),
        digest_sidecar_provider=sidecar_provider,
        cadence_seconds=900,
        boundary_events=(TASK_BOUNDARY,),
    )


def agent_message_boundary_decision(
    *,
    packets: Sequence[object] | object,
    actor: str,
    actor_role: str = "",
    session_id: str = "",
    target_ref: str = "",
    policy: PeerAwarenessPolicy | None = None,
    peer_provider: str = "",
    boundary_at_utc: str = "",
    last_peer_poll_at_utc: str = "",
    pending_packet_count: int = 0,
) -> PeerAwarenessDecision:
    """Run packet-body and peer-poll checks for an agent_message emit boundary."""
    resolved_policy = policy or default_peer_awareness_policy(
        role=actor_role,
        work_class="interactive_turn",
        peer_provider=peer_provider,
    )
    blocking_packet = blocking_body_packet(
        packets,
        actor=actor,
        actor_role=resolved_policy.role if not actor_role else actor_role,
        session_id=session_id,
        target_ref=target_ref,
    )
    if blocking_packet is not None:
        packet_id = _text(blocking_packet.get("packet_id"))
        return PeerAwarenessDecision(
            action="open_packet_body",
            reason="packet_body_unobserved_at_agent_message_emit",
            peer_provider=resolved_policy.peer_provider,
            cadence_seconds=resolved_policy.cadence_seconds,
            body_open_required=True,
            blocking_packet_id=packet_id,
            next_commands=(
                packet_body_show_command(
                    blocking_packet,
                    actor=actor,
                    actor_role=actor_role,
                    session_id=session_id,
                ),
            ),
        )
    if peer_poll_due(
        policy=resolved_policy,
        boundary_at_utc=boundary_at_utc,
        last_peer_poll_at_utc=last_peer_poll_at_utc,
        pending_packet_count=pending_packet_count,
        agent_message_boundary=AGENT_MESSAGE_EMIT_BOUNDARY,
        long_running_work_classes=_LONG_RUNNING_WORK_CLASSES,
    ):
        sidecar_provider = (
            resolved_policy.digest_sidecar_provider
            or resolved_policy.peer_provider
            or peer_provider
        )
        action = (
            "launch_digest_sidecar"
            if resolved_policy.digest_sidecar_enabled
            else "poll_peer_state"
        )
        reason = (
            "digest_sidecar_due_at_agent_message_emit"
            if resolved_policy.digest_sidecar_enabled
            else "peer_poll_due_at_agent_message_emit"
        )
        return PeerAwarenessDecision(
            action=action,
            reason=reason,
            peer_provider=resolved_policy.peer_provider,
            cadence_seconds=resolved_policy.cadence_seconds,
            poll_due=True,
            sidecar_required=resolved_policy.digest_sidecar_enabled,
            sidecar_provider=sidecar_provider,
            next_commands=peer_poll_commands(
                actor=actor,
                peer_provider=sidecar_provider,
            ),
        )
    return PeerAwarenessDecision(
        action="continue_current_work",
        reason="peer_awareness_current",
        peer_provider=resolved_policy.peer_provider,
        cadence_seconds=resolved_policy.cadence_seconds,
    )


def peer_poll_commands(*, actor: str, peer_provider: str) -> tuple[str, str]:
    """Return the two explicit poll commands required by PeerAwarenessPolicy."""
    target_actor = _text(actor) or "codex"
    peer = _text(peer_provider) or "claude"
    return (
        "python3 dev/scripts/devctl.py review-channel --action inbox "
        f"--target {target_actor} --actor {target_actor} --status pending "
        "--terminal none --format md",
        "python3 dev/scripts/devctl.py agent-mind "
        f"--agent {peer} --since-cursor --project --format md --limit 20",
    )


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "AGENT_MESSAGE_EMIT_BOUNDARY",
    "PACKET_BODY_OBSERVATION",
    "PEER_AGENT_MIND_OBSERVATION",
    "PEER_AWARENESS_DECISION_CONTRACT_ID",
    "PEER_AWARENESS_OBSERVATION_CONTRACT_ID",
    "PEER_AWARENESS_POLICY_CONTRACT_ID",
    "PEER_AWARENESS_POLICY_SCHEMA_VERSION",
    "REVIEW_CHANNEL_INBOX_OBSERVATION",
    "SUBPROCESS_HEARTBEAT_BOUNDARY",
    "TASK_BOUNDARY",
    "PeerAwarenessDecision",
    "PeerAwarenessPolicy",
    "agent_message_boundary_decision",
    "default_peer_awareness_policy",
    "peer_poll_commands",
]
