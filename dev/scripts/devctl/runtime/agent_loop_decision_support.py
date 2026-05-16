"""Branch decision helpers for AgentLoopDecision."""

from __future__ import annotations

from collections.abc import Mapping
from ..review_channel.agent_packet_focus import packet_by_id
from ..review_channel.agent_packet_attention import packet_body_open_command
from ..review_channel.packet_loop_attention import packet_body_attention_required
from .agent_loop_blocker_actions import required_action_for_blocker
from .agent_loop_decision_builder import (
    CONTINUE_TO_GOAL_ACTION,
    SCOPED_IMPLEMENTATION_EDIT_ACTION,
    attention_reason,
    body_open_decision,
    body_open_required,
    decision,
    decision_from_loop_state,
    lifecycle_from_loop_state,
    next_command_for_turn,
    readable_decision_fields,
)
from .agent_loop_decision_models import AgentLoopDecision
from .session_termination_policy import TaskCompleteDecision
from .value_coercion import (
    coerce_bool,
    coerce_text as _text,
)
from .agent_loop_decision_sources import (
    AgentLoopContext,
    PacketState,
)

def actor_identity_decision(ctx: AgentLoopContext) -> AgentLoopDecision:
    return decision(ctx, "blocked", "provide_actor_identity", "actor_identity_required")


def session_identity_decision(ctx: AgentLoopContext) -> AgentLoopDecision:
    return decision(ctx, "blocked", "provide_session_identity", "session_identity_required")


def blocker_decision(ctx: AgentLoopContext, packets: PacketState) -> AgentLoopDecision:
    return decision(
        ctx,
        "blocked",
        required_action_for_blocker(ctx.top_blocker, next_action=ctx.next_action),
        ctx.top_blocker,
        should_continue_loop=True,
        active_packet_id=packets.active_packet_id,
        attention_packet_id=packets.attention_packet_id,
        executing_packet_id=packets.executing_packet_id,
        legacy_unscoped_packet_id=packets.legacy_unscoped_packet_id,
        plan_target_ref=_text(packets.active_packet.get("target_ref")),
        may_mutate=ctx.may_mutate,
    )


def communication_attention_decision(
    ctx: AgentLoopContext,
    packets: PacketState,
) -> AgentLoopDecision:
    pivot_packet_id = packets.attention_packet_id or packets.active_packet_id
    pivot_packet = packet_by_id(ctx.review_state, pivot_packet_id)
    if body_open_required(ctx):
        return body_open_decision(ctx, packets, pivot_packet_id, pivot_packet)
    return decision(
        ctx,
        "blocked",
        CONTINUE_TO_GOAL_ACTION,
        attention_reason(ctx) or "packet_attention_before_blocker",
        lifecycle_state="needs_attention",
        decision_code=CONTINUE_TO_GOAL_ACTION,
        reason_code="peer_input_before_blocker",
        should_continue_loop=True,
        safe_to_continue=False,
        may_mutate=False,
        active_packet_id=pivot_packet_id,
        attention_packet_id=packets.attention_packet_id,
        executing_packet_id=packets.executing_packet_id,
        legacy_unscoped_packet_id=packets.legacy_unscoped_packet_id,
        plan_target_ref=_text(pivot_packet.get("target_ref")),
    )


def attention_decision(ctx: AgentLoopContext, packets: PacketState) -> AgentLoopDecision:
    pivot_packet_id = packets.attention_packet_id or packets.active_packet_id
    pivot_packet = packet_by_id(ctx.review_state, pivot_packet_id)
    if body_open_required(ctx):
        return body_open_decision(ctx, packets, pivot_packet_id, pivot_packet)
    return decision(
        ctx,
        "work",
        CONTINUE_TO_GOAL_ACTION,
        attention_reason(ctx) or "peer_input_required",
        lifecycle_state="needs_attention",
        decision_code=CONTINUE_TO_GOAL_ACTION,
        reason_code="peer_input_required",
        should_continue_loop=True,
        safe_to_continue=True,
        may_mutate=ctx.may_mutate,
        active_packet_id=pivot_packet_id,
        attention_packet_id=packets.attention_packet_id,
        executing_packet_id=packets.executing_packet_id,
        plan_target_ref=_text(pivot_packet.get("target_ref")),
    )


def completed_decision(ctx: AgentLoopContext, outcome: Mapping[str, object]) -> AgentLoopDecision:
    return decision(
        ctx,
        "done",
        "stop_no_work",
        _text(outcome.get("reason")) or "completed_handoff",
        lifecycle_state="completed",
        decision_code="stop_no_work",
        reason_code="completed_handoff",
    )


def continuation_anchor_decision(
    ctx: AgentLoopContext,
    task_decision: TaskCompleteDecision,
) -> AgentLoopDecision:
    return decision(
        ctx,
        "work",
        "continue_from_continuation_anchor",
        task_decision.reason,
        lifecycle_state="needs_attention",
        decision_code="continue_from_continuation_anchor",
        reason_code=task_decision.reason,
        should_continue_loop=True,
        safe_to_continue=True,
        may_mutate=ctx.may_mutate,
        active_packet_id=task_decision.anchor_packet_id,
        next_command_override=task_decision.next_command,
    )


def continuation_anchor_missing_decision(
    ctx: AgentLoopContext,
    task_decision: TaskCompleteDecision,
) -> AgentLoopDecision:
    return decision(
        ctx,
        "blocked",
        "post_continuation_anchor",
        task_decision.reason,
        lifecycle_state="blocked",
        decision_code="run_next_command",
        reason_code=task_decision.error_kind or task_decision.reason,
        should_continue_loop=True,
        safe_to_continue=False,
        may_mutate=False,
        next_command_override=task_decision.next_command,
    )


def pending_review_packet_decision(
    ctx: AgentLoopContext,
    task_decision: TaskCompleteDecision,
) -> AgentLoopDecision:
    packet_id = task_decision.blocking_packet_id
    return decision(
        ctx,
        "blocked",
        CONTINUE_TO_GOAL_ACTION,
        task_decision.reason,
        lifecycle_state="needs_attention",
        decision_code=CONTINUE_TO_GOAL_ACTION,
        reason_code=task_decision.error_kind or task_decision.reason,
        should_continue_loop=True,
        safe_to_continue=False,
        may_mutate=False,
        active_packet_id=packet_id,
        attention_packet_id=packet_id,
        next_command_override=task_decision.next_command,
    )


def requested_packet_body_open_required(
    ctx: AgentLoopContext,
    packets: PacketState,
) -> bool:
    """Return whether an exact packet target still needs body observation."""
    if not ctx.requested_packet_id:
        return False
    packet = packets.attention_packet or packets.active_packet
    if not packet:
        return False
    return packet_body_attention_required(
        packet,
        actor=ctx.actor,
        role=ctx.role,
        session=ctx.session,
    )


def requested_packet_body_open_decision(
    ctx: AgentLoopContext,
    packets: PacketState,
) -> AgentLoopDecision:
    packet_id = packets.attention_packet_id or packets.active_packet_id
    packet = packets.attention_packet or packets.active_packet
    return body_open_decision(
        ctx,
        packets,
        packet_id,
        packet,
        next_command_override=packet_body_open_command(
            packet_id=packet_id,
            actor=ctx.actor,
            role=ctx.role,
            session=ctx.session,
        ),
    )


def packet_attention_pending_decision(
    ctx: AgentLoopContext,
    task_decision: TaskCompleteDecision,
) -> AgentLoopDecision:
    packet_id = task_decision.blocking_packet_id
    return decision(
        ctx,
        "blocked",
        CONTINUE_TO_GOAL_ACTION,
        task_decision.reason,
        lifecycle_state="needs_attention",
        decision_code=CONTINUE_TO_GOAL_ACTION,
        reason_code=task_decision.error_kind or task_decision.reason,
        should_continue_loop=True,
        safe_to_continue=False,
        may_mutate=False,
        active_packet_id=packet_id,
        attention_packet_id=packet_id,
        next_command_override=task_decision.next_command,
    )


def unresolved_decision(ctx: AgentLoopContext, outcome: Mapping[str, object]) -> AgentLoopDecision:
    outcome_kind = _text(outcome.get("outcome")) or "session_unresolved"
    return decision(
        ctx,
        "blocked",
        "resume_or_recover_session",
        _text(outcome.get("reason")) or outcome_kind,
        lifecycle_state="unresolved",
        decision_code="resume_or_recover",
        reason_code=outcome_kind,
        should_continue_loop=True,
    )


def executing_decision(ctx: AgentLoopContext, packets: PacketState) -> AgentLoopDecision:
    return decision(
        ctx,
        "work",
        "continue_current_execution",
        "executing_packet",
        lifecycle_state="executing",
        decision_code="continue_current_execution",
        reason_code="executing_packet",
        should_continue_loop=True,
        safe_to_continue=True,
        may_mutate=ctx.may_mutate,
        active_packet_id=packets.active_packet_id,
        attention_packet_id=packets.attention_packet_id,
        executing_packet_id=packets.executing_packet_id,
        plan_target_ref=_text(packets.executing_packet.get("target_ref")),
    )


def active_packet_decision(ctx: AgentLoopContext, packets: PacketState) -> AgentLoopDecision:
    return decision(
        ctx,
        "work",
        "execute_active_packet",
        "active_packet",
        lifecycle_state="needs_attention",
        decision_code=CONTINUE_TO_GOAL_ACTION,
        reason_code="active_packet",
        should_continue_loop=True,
        safe_to_continue=True,
        may_mutate=ctx.may_mutate,
        active_packet_id=packets.active_packet_id,
        attention_packet_id=packets.attention_packet_id,
        executing_packet_id=packets.executing_packet_id,
        plan_target_ref=_text(packets.active_packet.get("target_ref")),
    )


def observer_decision(ctx: AgentLoopContext, packets: PacketState) -> AgentLoopDecision:
    reason = (
        "legacy_unscoped_packet_not_observer_authority"
        if packets.legacy_unscoped_packet_id
        else "observer_lane"
    )
    return decision(
        ctx,
        "observe",
        "observe_typed_runtime",
        reason,
        lifecycle_state="idle",
        decision_code="wait",
        reason_code=reason,
        should_continue_loop=True,
        safe_to_continue=True,
        legacy_unscoped_packet_id=packets.legacy_unscoped_packet_id,
    )


def operator_override_plan_edit_decision(
    ctx: AgentLoopContext,
) -> AgentLoopDecision:
    return decision(
        ctx,
        "work",
        SCOPED_IMPLEMENTATION_EDIT_ACTION,
        "operator_override_plan_target",
        lifecycle_state="needs_attention",
        decision_code=CONTINUE_TO_GOAL_ACTION,
        reason_code="operator_override_edit_only_plan_target",
        should_continue_loop=True,
        safe_to_continue=True,
        may_mutate=ctx.may_mutate,
        plan_target_ref=ctx.requested_plan_ref,
    )


def wait_decision(ctx: AgentLoopContext) -> AgentLoopDecision:
    return decision(
        ctx,
        "wait",
        "wait_for_scoped_packet",
        "no_scoped_active_packet",
        lifecycle_state="waiting",
        decision_code="wait",
        reason_code="no_scoped_active_packet",
        should_continue_loop=True,
        safe_to_continue=True,
    )




__all__ = [
    "active_packet_decision",
    "actor_identity_decision",
    "attention_decision",
    "blocker_decision",
    "communication_attention_decision",
    "completed_decision",
    "CONTINUE_TO_GOAL_ACTION",
    "continuation_anchor_decision",
    "continuation_anchor_missing_decision",
    "executing_decision",
    "observer_decision",
    "operator_override_plan_edit_decision",
    "packet_attention_pending_decision",
    "pending_review_packet_decision",
    "requested_packet_body_open_decision",
    "requested_packet_body_open_required",
    "session_identity_decision",
    "next_command_for_turn",
    "unresolved_decision",
    "wait_decision",
]
