"""Peer digest sidecar decision support for AgentLoopDecision."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_loop_decision_builder import decision
from .agent_loop_decision_models import AgentLoopDecision
from .agent_loop_decision_sources import AgentLoopContext, PacketState
from .peer_awareness_policy import (
    PeerAwarenessPolicy,
    agent_message_boundary_decision,
    default_peer_awareness_policy,
)
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping as _mapping,
    coerce_text as _text,
)


def peer_digest_sidecar_decision(
    ctx: AgentLoopContext,
    packets: PacketState,
) -> AgentLoopDecision | None:
    """Return a digest-sidecar gate when the typed policy toggle is enabled."""
    awareness = _peer_digest_awareness_decision(ctx)
    if awareness.action != "launch_digest_sidecar":
        return None
    packet_id = (
        packets.attention_packet_id
        or packets.active_packet_id
        or _text(ctx.attention.get("latest_attention_packet_id"))
    )
    packet = packets.attention_packet or packets.active_packet or {}
    next_command = _digest_sidecar_command(awareness.next_commands)
    return decision(
        ctx,
        "blocked",
        "launch_peer_digest_sidecar",
        awareness.reason or "peer_digest_sidecar_required",
        lifecycle_state="needs_attention",
        decision_code="run_next_command",
        reason_code="peer_digest_sidecar_required",
        should_continue_loop=True,
        safe_to_continue=False,
        may_mutate=False,
        active_packet_id=packet_id,
        attention_packet_id=packet_id,
        executing_packet_id=packets.executing_packet_id,
        legacy_unscoped_packet_id=packets.legacy_unscoped_packet_id,
        plan_target_ref=_text(packet.get("target_ref")),
        next_command_override=next_command,
    )


def _peer_digest_awareness_decision(ctx: AgentLoopContext):
    policy = _peer_digest_policy(ctx)
    if policy is None or not _peer_digest_pressure(ctx):
        return agent_message_boundary_decision(
            packets=(),
            actor=ctx.actor,
            actor_role=ctx.role,
            session_id=ctx.session,
        )
    return agent_message_boundary_decision(
        packets=_packet_rows(ctx.review_state),
        actor=ctx.actor,
        actor_role=ctx.role,
        session_id=ctx.session,
        target_ref=ctx.requested_plan_ref,
        policy=policy,
        peer_provider=policy.peer_provider,
        boundary_at_utc=_boundary_at_utc(ctx),
        last_peer_poll_at_utc=_last_peer_poll_at_utc(ctx),
        pending_packet_count=coerce_int(ctx.attention.get("pending_packet_count")),
    )


def _peer_digest_policy(ctx: AgentLoopContext) -> PeerAwarenessPolicy | None:
    payload = _configured_peer_awareness_policy(ctx)
    if not _digest_sidecar_enabled(payload):
        return None
    peer_provider = _text(payload.get("peer_provider")) or _default_peer_provider(
        ctx.actor
    )
    return default_peer_awareness_policy(
        role=_text(payload.get("role")) or ctx.role,
        work_class=_text(payload.get("work_class")) or "long_running_subprocess",
        peer_provider=peer_provider,
        digest_sidecar_enabled=True,
        digest_sidecar_provider=(
            _text(payload.get("digest_sidecar_provider")) or peer_provider
        ),
    )


def _configured_peer_awareness_policy(
    ctx: AgentLoopContext,
) -> Mapping[str, object]:
    reviewer_runtime = _mapping(ctx.review_state.get("reviewer_runtime"))
    candidates = (
        ctx.review_state.get("peer_awareness_policy"),
        reviewer_runtime.get("peer_awareness_policy"),
        ctx.dashboard.get("peer_awareness_policy"),
    )
    for candidate in candidates:
        payload = _mapping(candidate)
        if payload:
            return payload
    return {}


def _digest_sidecar_enabled(payload: Mapping[str, object]) -> bool:
    if not payload:
        return False
    if coerce_bool(payload.get("digest_sidecar_enabled")):
        return True
    mode = _text(payload.get("digest_sidecar_mode")).lower().replace("-", "_")
    return mode in {"required", "enabled", "on", "sidecar", "sidecar_required"}


def _peer_digest_pressure(ctx: AgentLoopContext) -> bool:
    if coerce_int(ctx.attention.get("pending_packet_count")) > 0:
        return True
    if coerce_bool(ctx.attention.get("wake_required")):
        return True
    if coerce_bool(ctx.attention.get("pivot_required")):
        return True
    if _text(ctx.attention.get("latest_attention_packet_id")):
        return True
    return False


def _boundary_at_utc(ctx: AgentLoopContext) -> str:
    return (
        _text(ctx.clock.get("timestamp_utc"))
        or _text(ctx.clock.get("generated_at_utc"))
        or _text(ctx.clock.get("source_timestamp_utc"))
    )


def _last_peer_poll_at_utc(ctx: AgentLoopContext) -> str:
    policy_payload = _configured_peer_awareness_policy(ctx)
    direct = _text(policy_payload.get("last_peer_poll_at_utc"))
    if direct:
        return direct
    minds = _mapping(ctx.review_state.get("agent_minds")) or _mapping(
        ctx.dashboard.get("agent_minds")
    )
    actor_mind = _mapping(minds.get(ctx.actor))
    awareness = _mapping(actor_mind.get("peer_awareness"))
    return _text(awareness.get("last_peer_poll_at_utc"))


def _packet_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = review_state.get("packets")
    if not isinstance(rows, list):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _default_peer_provider(actor: str) -> str:
    normalized = _text(actor).lower()
    if normalized == "codex":
        return "claude"
    if normalized == "claude":
        return "codex"
    return "codex"


def _digest_sidecar_command(commands: tuple[str, ...]) -> str:
    """Prefer the command that refreshes peer agent-mind digest state.

    Packet-body gates run before the digest-sidecar gate. If we return the
    inbox command here, the loop can keep listing packets without producing
    the peer-mind observation required to unblock blind continuation.
    """
    for command in commands:
        if "agent-mind" in command:
            return command
    return commands[0] if commands else ""


__all__ = ["peer_digest_sidecar_decision"]
