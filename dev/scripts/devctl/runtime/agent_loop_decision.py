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
    packet_attention_pending_decision,
    pending_review_packet_decision,
    session_identity_decision,
    unresolved_decision,
    wait_decision,
)
from .agent_loop_decision_sources import (
    attention_requires_pivot,
    blocker_active,
    build_agent_loop_context,
    latest_session_outcome,
    resolve_packet_state,
    role_is_observer,
    session_identity_required,
)
from .session_termination_policy import (
    session_termination_policy_from_review_state,
    task_complete_decision,
)


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
    if not ctx.actor:
        return actor_identity_decision(ctx)
    if session_identity_required(ctx):
        return session_identity_decision(ctx)

    packets = resolve_packet_state(ctx)
    outcome = latest_session_outcome(ctx)
    outcome_kind = str(outcome.get("outcome") or "").strip()
    if blocker_active(ctx) and attention_requires_pivot(ctx, packets):
        return communication_attention_decision(ctx, packets)
    if blocker_active(ctx):
        return blocker_decision(ctx, packets)

    if outcome_kind == "completed_handoff":
        task_decision = task_complete_decision(
            session_id=ctx.session,
            packets=review_state.get("packets", ()),
            policy=session_termination_policy_from_review_state(review_state),
            actor=ctx.actor,
            actor_role=ctx.role,
            packet_attention=ctx.attention,
        )
        if task_decision.packet_attention_pending:
            return packet_attention_pending_decision(ctx, task_decision)
        if task_decision.pending_review_packet:
            return pending_review_packet_decision(ctx, task_decision)
        if packets.active_packet_id:
            return active_packet_decision(ctx, packets)
        if task_decision.continuation_anchor_missing:
            return continuation_anchor_missing_decision(ctx, task_decision)
        if not task_decision.terminate:
            return continuation_anchor_decision(ctx, task_decision)
        return completed_decision(ctx, outcome)
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
    return wait_decision(ctx)


__all__ = ["AgentLoopDecision", "build_agent_loop_decision"]
