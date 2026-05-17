"""Typed per-agent loop decision over shared runtime state."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_loop_decision_models import AgentLoopDecision
from .agent_loop_decision_support import (
    active_packet_decision,
    actor_identity_decision,
    attention_decision,
    blocker_decision,
    communication_attention_decision,
    completed_decision,
    continuation_anchor_decision,
    continuation_anchor_missing_decision,
    executing_decision,
    observer_decision,
    operator_override_plan_edit_decision,
    packet_attention_pending_decision,
    pending_review_packet_decision,
    requested_packet_body_open_decision,
    requested_packet_body_open_required,
    session_identity_decision,
    unresolved_decision,
    wait_decision,
)
from .agent_loop_decision_sources import (
    AgentLoopContext,
    PacketState,
    attention_requires_pivot,
    blocker_active,
    build_agent_loop_context,
    latest_session_outcome,
    resolve_packet_state,
    role_is_observer,
    session_identity_required,
)
from .agent_loop_peer_digest_sidecar import peer_digest_sidecar_decision
from .session_termination_policy import (
    session_termination_policy_from_review_state,
    task_complete_decision,
)
from .task_complete_result import (
    TaskCompleteBodyObservationRequired,
    TaskCompleteContinuationActive,
    TaskCompleteContinuationMissing,
    TaskCompletePacketAttentionPending,
    TaskCompletePendingReview,
    TaskCompleteTerminated,
    task_complete_result,
)
from .typing_compat import assert_never


def _identity_gate_decision(ctx: AgentLoopContext) -> AgentLoopDecision | None:
    if not ctx.actor:
        return actor_identity_decision(ctx)
    if session_identity_required(ctx):
        return session_identity_decision(ctx)
    return None


def _packet_or_blocker_decision(
    ctx: AgentLoopContext,
    packets: PacketState,
) -> AgentLoopDecision | None:
    if requested_packet_body_open_required(ctx, packets):
        return requested_packet_body_open_decision(ctx, packets)
    if not blocker_active(ctx):
        return None
    if attention_requires_pivot(ctx, packets):
        return communication_attention_decision(ctx, packets)
    return blocker_decision(ctx, packets)


def _completed_handoff_decision(
    ctx: AgentLoopContext,
    *,
    review_state: Mapping[str, object],
    packets: PacketState,
    outcome: Mapping[str, object],
) -> AgentLoopDecision:
    task_decision = task_complete_decision(
        session_id=ctx.session,
        packets=review_state.get("packets", ()),
        policy=session_termination_policy_from_review_state(review_state),
        actor=ctx.actor,
        actor_role=ctx.role,
        target_ref=ctx.requested_plan_ref,
        packet_attention=ctx.attention,
    )
    task_result = task_complete_result(task_decision)
    match task_result:
        case TaskCompletePacketAttentionPending(decision=decision):
            return packet_attention_pending_decision(ctx, decision)
        case TaskCompleteBodyObservationRequired(decision=decision):
            return pending_review_packet_decision(ctx, decision)
        case TaskCompletePendingReview(decision=decision):
            return pending_review_packet_decision(ctx, decision)
        case (
            TaskCompleteContinuationMissing()
            | TaskCompleteContinuationActive()
            | TaskCompleteTerminated()
        ):
            pass
    if packets.active_packet_id:
        return active_packet_decision(ctx, packets)
    match task_result:
        case TaskCompleteContinuationMissing(decision=decision):
            return continuation_anchor_missing_decision(ctx, decision)
        case TaskCompleteContinuationActive(decision=decision):
            return continuation_anchor_decision(ctx, decision)
        case TaskCompleteTerminated():
            return completed_decision(ctx, outcome)
        case (
            TaskCompletePacketAttentionPending()
            | TaskCompleteBodyObservationRequired()
            | TaskCompletePendingReview()
        ):
            raise AssertionError("task_complete_blocking_result_not_returned")
    assert_never(task_result)


def _active_runtime_decision(
    ctx: AgentLoopContext,
    *,
    packets: PacketState,
    outcome: Mapping[str, object],
    outcome_kind: str,
) -> AgentLoopDecision:
    if attention_requires_pivot(ctx, packets):
        return attention_decision(ctx, packets)
    if outcome_kind in {"unresolved", "process_died"} and not packets.active_packet_id:
        return unresolved_decision(ctx, outcome)
    if packets.executing_packet_id:
        return executing_decision(ctx, packets)
    if packets.active_packet_id:
        return active_packet_decision(ctx, packets)
    if role_is_observer(ctx.role):
        return observer_decision(ctx, packets)
    if (
        ctx.operator_override.edit_allowed
        and ctx.operator_override.target_kind == "plan"
        and ctx.requested_plan_ref
    ):
        return operator_override_plan_edit_decision(ctx)
    return wait_decision(ctx)


def build_agent_loop_decision(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    actor_id: object,
    actor_role: object = "",
    session_id: object = "",
    loop_intent: object = "",
    requested_plan_ref: object = "",
    requested_packet_id: object = "",
    master_plan: object = None,
    operator_override_requested: object = False,
    operator_override_reason: object = "",
    operator_override_scope: object = "edit-only",
    operator_override_by: object = "operator",
) -> AgentLoopDecision:
    """Resolve what one agent session should do from typed state."""
    ctx = build_agent_loop_context(
        review_state=review_state,
        dashboard=dashboard,
        actor_id=actor_id,
        actor_role=actor_role,
        session_id=session_id,
        loop_intent=loop_intent,
        requested_plan_ref=requested_plan_ref,
        requested_packet_id=requested_packet_id,
        master_plan=master_plan,
        operator_override_requested=operator_override_requested,
        operator_override_reason=operator_override_reason,
        operator_override_scope=operator_override_scope,
        operator_override_by=operator_override_by,
    )
    identity_decision = _identity_gate_decision(ctx)
    if identity_decision is not None:
        return identity_decision

    packets = resolve_packet_state(ctx)
    outcome = latest_session_outcome(ctx)
    outcome_kind = str(outcome.get("outcome") or "").strip()
    gate_decision = _packet_or_blocker_decision(ctx, packets)
    if gate_decision is not None:
        return gate_decision
    digest_decision = peer_digest_sidecar_decision(ctx, packets)
    if digest_decision is not None:
        return digest_decision

    if outcome_kind == "completed_handoff":
        return _completed_handoff_decision(
            ctx,
            review_state=review_state,
            packets=packets,
            outcome=outcome,
        )
    return _active_runtime_decision(
        ctx,
        packets=packets,
        outcome=outcome,
        outcome_kind=outcome_kind,
    )


__all__ = ["AgentLoopDecision", "build_agent_loop_decision"]
