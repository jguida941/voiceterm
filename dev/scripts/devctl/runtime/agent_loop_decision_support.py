"""Branch decision helpers for AgentLoopDecision."""

from __future__ import annotations

from collections.abc import Mapping

from ..review_channel.agent_packet_focus import packet_by_id
from .agent_loop_decision_models import AgentLoopDecision
from .agent_loop_operator_override import operator_override_next_command
from .agent_loop_policy import policy_for_turn
from .value_coercion import coerce_bool, coerce_int, coerce_text as _text
from .agent_loop_decision_sources import (
    AgentLoopContext,
    PacketState,
    required_action_for_blocker,
)


def actor_identity_decision(ctx: AgentLoopContext) -> AgentLoopDecision:
    return decision(ctx, "blocked", "provide_actor_identity", "actor_identity_required")


def session_identity_decision(ctx: AgentLoopContext) -> AgentLoopDecision:
    return decision(ctx, "blocked", "provide_session_identity", "session_identity_required")


def blocker_decision(ctx: AgentLoopContext, packets: PacketState) -> AgentLoopDecision:
    return decision(
        ctx,
        "blocked",
        required_action_for_blocker(ctx.top_blocker),
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
    return decision(
        ctx,
        "blocked",
        "triage_pending_packet",
        _text(ctx.attention.get("stale_reason")) or "packet_attention_before_blocker",
        lifecycle_state="needs_attention",
        decision_code="pivot_to_packet",
        reason_code="packet_attention_before_blocker",
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
    return decision(
        ctx,
        "work",
        "pivot_to_attention_packet",
        _text(ctx.attention.get("stale_reason")) or "wake_required",
        lifecycle_state="needs_attention",
        decision_code="pivot_to_packet",
        reason_code="wake_required",
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
        decision_code="pivot_to_packet",
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


def decision(
    ctx: AgentLoopContext,
    loop_state: str,
    required_action: str,
    reason: str,
    *,
    lifecycle_state: str = "",
    decision_code: str = "",
    reason_code: str = "",
    should_continue_loop: bool = False,
    safe_to_continue: bool = False,
    may_mutate: bool = False,
    active_packet_id: str = "",
    attention_packet_id: str = "",
    executing_packet_id: str = "",
    legacy_unscoped_packet_id: str = "",
    plan_target_ref: str = "",
) -> AgentLoopDecision:
    resolved_lifecycle = lifecycle_state or lifecycle_from_loop_state(loop_state)
    resolved_decision = decision_code or decision_from_loop_state(loop_state)
    resolved_reason_code = reason_code or required_action
    loop_policy = policy_for_turn(
        ctx=ctx,
        loop_state=loop_state,
        required_action=required_action,
        decision_code=resolved_decision,
        safe_to_continue=safe_to_continue,
        should_continue_loop=should_continue_loop,
        active_packet_id=active_packet_id,
        plan_target_ref=plan_target_ref,
    )
    effective_may_mutate = may_mutate or (
        ctx.operator_override.edit_allowed
        and required_action == "repair_startup_authority"
    )
    override_next = operator_override_next_command(ctx.operator_override)
    if override_next and required_action == "repair_startup_authority":
        next_command = override_next
    elif required_action == "stop_no_work" or not loop_policy.can_run_next_command:
        next_command = ""
    else:
        next_command = ctx.next_command
    return AgentLoopDecision(
        actor_id=ctx.actor,
        actor_role=ctx.role,
        session_id=ctx.session,
        loop_state=loop_state,
        required_action=required_action,
        lifecycle_state=resolved_lifecycle,
        decision=resolved_decision,
        reason_code=resolved_reason_code,
        loop_mode=loop_policy.loop_mode,
        loop_driver_agent=loop_policy.loop_driver_agent,
        wake_source=loop_policy.wake_source,
        loop_intent=loop_policy.loop_intent,
        target_kind=loop_policy.target_kind,
        target_ref=loop_policy.target_ref,
        recommended_cadence_seconds=loop_policy.recommended_cadence_seconds,
        can_run_next_command=loop_policy.can_run_next_command,
        dogfood_record_allowed=loop_policy.dogfood_record_allowed,
        advance_allowed=loop_policy.advance_allowed,
        proof_state=loop_policy.proof_state,
        required_proofs=loop_policy.required_proofs,
        satisfied_proofs=loop_policy.satisfied_proofs,
        missing_proofs=loop_policy.missing_proofs,
        policy_reason=loop_policy.policy_reason,
        next_loop_command=loop_policy.next_loop_command,
        should_continue_loop=should_continue_loop,
        safe_to_continue=safe_to_continue,
        may_mutate=effective_may_mutate,
        reason=reason,
        next_command=next_command,
        next_action=ctx.next_action,
        top_blocker=ctx.top_blocker,
        active_packet_id=active_packet_id,
        attention_packet_id=attention_packet_id,
        executing_packet_id=executing_packet_id,
        legacy_unscoped_packet_id=legacy_unscoped_packet_id,
        plan_target_ref=plan_target_ref,
        current_instruction_revision=ctx.current_instruction_revision,
        wake_required=coerce_bool(ctx.attention.get("wake_required")),
        pivot_required=coerce_bool(ctx.attention.get("pivot_required")),
        pending_packet_count=coerce_int(ctx.attention.get("pending_packet_count")),
        latest_inbox_event_id=_text(ctx.attention.get("latest_inbox_event_id")),
        last_observed_event_id=_text(ctx.attention.get("last_observed_event_id")),
        allowed_actions=ctx.allowed_actions,
        blocked_actions=ctx.blocked_actions,
        granted_capabilities=ctx.granted_capabilities,
        operator_override=ctx.operator_override,
        source_latest_event_id=_text(ctx.clock.get("source_latest_event_id")),
        source_snapshot_id=_text(ctx.clock.get("snapshot_id")),
    )


def lifecycle_from_loop_state(loop_state: str) -> str:
    return {
        "blocked": "blocked",
        "work": "needs_attention",
        "observe": "idle",
        "wait": "waiting",
        "done": "completed",
    }.get(loop_state, "blocked")


def decision_from_loop_state(loop_state: str) -> str:
    return {
        "blocked": "run_next_command",
        "work": "pivot_to_packet",
        "observe": "wait",
        "wait": "wait",
        "done": "stop_no_work",
    }.get(loop_state, "run_next_command")


__all__ = [
    "active_packet_decision",
    "actor_identity_decision",
    "attention_decision",
    "blocker_decision",
    "communication_attention_decision",
    "completed_decision",
    "executing_decision",
    "observer_decision",
    "session_identity_decision",
    "unresolved_decision",
    "wait_decision",
]
