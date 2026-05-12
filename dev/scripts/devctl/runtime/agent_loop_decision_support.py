"""Branch decision helpers for AgentLoopDecision."""

from __future__ import annotations

from collections.abc import Mapping

from ..review_channel.agent_packet_focus import packet_by_id
from .agent_loop_blocker_actions import required_action_for_blocker
from .agent_loop_command import scoped_operator_override_command
from .agent_loop_decision_models import AgentLoopDecision
from .agent_loop_operator_override import operator_override_next_command
from .agent_loop_policy import policy_for_turn
from .session_termination_policy import TaskCompleteDecision
from .value_coercion import coerce_bool, coerce_int, coerce_text as _text
from .agent_loop_decision_sources import (
    AgentLoopContext,
    PacketState,
)

CONTINUE_TO_GOAL_ACTION = "continue_to_goal"


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
    if _body_open_required(ctx):
        return _body_open_decision(ctx, packets, pivot_packet_id, pivot_packet)
    return decision(
        ctx,
        "blocked",
        CONTINUE_TO_GOAL_ACTION,
        _attention_reason(ctx) or "packet_attention_before_blocker",
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
    if _body_open_required(ctx):
        return _body_open_decision(ctx, packets, pivot_packet_id, pivot_packet)
    return decision(
        ctx,
        "work",
        CONTINUE_TO_GOAL_ACTION,
        _attention_reason(ctx) or "peer_input_required",
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
    next_command_override: str = "",
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
    effective_should_continue_loop = should_continue_loop or (
        required_action == "stop_no_work" and not loop_policy.advance_allowed
    )
    effective_may_mutate = may_mutate or (
        ctx.operator_override.edit_allowed
        and required_action == "repair_startup_authority"
    )
    next_command = next_command_for_turn(
        ctx=ctx,
        loop_policy=loop_policy,
        loop_state=loop_state,
        required_action=required_action,
        should_continue_loop=effective_should_continue_loop,
        reason=reason,
        next_command_override=next_command_override,
    )
    readable = readable_decision_fields(
        required_action=required_action,
        reason=reason,
        active_packet_id=active_packet_id,
        attention_packet_id=attention_packet_id,
        plan_target_ref=plan_target_ref,
        should_continue_loop=effective_should_continue_loop,
        next_command=next_command,
    )
    return AgentLoopDecision(
        actor_id=ctx.actor,
        actor_role=ctx.role,
        session_id=ctx.session,
        effective_actor_role=ctx.operator_override.effective_actor_role or ctx.role,
        effective_workstream_id=ctx.operator_override.effective_workstream_id,
        effective_authority_source=ctx.operator_override.effective_authority_source,
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
        should_continue_loop=effective_should_continue_loop,
        safe_to_continue=safe_to_continue,
        may_mutate=effective_may_mutate,
        reason=reason,
        next_command=next_command,
        next_action=ctx.next_action,
        top_blocker=ctx.top_blocker,
        user_action=readable["user_action"],
        continuation_goal=readable["continuation_goal"],
        why_not_done=readable["why_not_done"],
        user_continue_state=readable["user_continue_state"],
        new_peer_input=coerce_bool(ctx.attention.get("wake_required")),
        switch_to_packet_goal=coerce_bool(ctx.attention.get("pivot_required")),
        continue_before_final=effective_should_continue_loop,
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


def next_command_for_turn(
    *,
    ctx: object,
    loop_policy: object,
    loop_state: str,
    required_action: str,
    should_continue_loop: bool,
    reason: str,
    next_command_override: str = "",
) -> str:
    """Return the command a simple loop driver should run next."""
    override_next = operator_override_next_command(ctx.operator_override)
    override_request_next = scoped_operator_override_command(ctx, reason=reason)
    if next_command_override:
        return next_command_override
    if override_next and required_action == "repair_startup_authority":
        return override_next
    if (
        override_request_next
        and loop_state == "blocked"
        and not ctx.may_mutate
        and not ctx.operator_override.requested
    ):
        return override_request_next
    if required_action == "stop_no_work":
        if (
            should_continue_loop
            and not loop_policy.advance_allowed
            and loop_policy.next_loop_command
        ):
            return loop_policy.next_loop_command
        return ""
    if loop_policy.can_run_next_command:
        return ctx.next_command
    if should_continue_loop and loop_policy.next_loop_command:
        return loop_policy.next_loop_command
    return ""


def decision_from_loop_state(loop_state: str) -> str:
    return {
        "blocked": "run_next_command",
        "work": CONTINUE_TO_GOAL_ACTION,
        "observe": "wait",
        "wait": "wait",
        "done": "stop_no_work",
    }.get(loop_state, "run_next_command")


def _attention_reason(ctx: AgentLoopContext) -> str:
    reason = _text(ctx.attention.get("stale_reason"))
    if reason == "wake_required":
        return "peer_input_required"
    if reason == "actor_identity_ambiguous_with_pending_wake":
        return "actor_identity_ambiguous_with_pending_peer_input"
    return reason


def _body_open_required(ctx: AgentLoopContext) -> bool:
    return coerce_bool(ctx.attention.get("body_open_required"))


def _body_open_command(ctx: AgentLoopContext) -> str:
    return _text(ctx.attention.get("body_open_command"))


def _body_open_decision(
    ctx: AgentLoopContext,
    packets: PacketState,
    pivot_packet_id: str,
    pivot_packet: Mapping[str, object],
) -> AgentLoopDecision:
    packet_id = _text(ctx.attention.get("body_open_packet_id")) or pivot_packet_id
    return decision(
        ctx,
        "blocked",
        "open_packet_body",
        _attention_reason(ctx) or "packet_body_open_required",
        lifecycle_state="needs_attention",
        decision_code="run_next_command",
        reason_code="packet_body_open_required",
        should_continue_loop=True,
        safe_to_continue=False,
        may_mutate=False,
        active_packet_id=packet_id,
        attention_packet_id=packet_id or packets.attention_packet_id,
        executing_packet_id=packets.executing_packet_id,
        legacy_unscoped_packet_id=packets.legacy_unscoped_packet_id,
        plan_target_ref=_text(pivot_packet.get("target_ref")),
        next_command_override=_body_open_command(ctx),
    )


def readable_decision_fields(
    *,
    required_action: str,
    reason: str,
    active_packet_id: str,
    attention_packet_id: str,
    plan_target_ref: str,
    should_continue_loop: bool,
    next_command: str,
) -> dict[str, str]:
    packet_id = attention_packet_id or active_packet_id
    goal = plan_target_ref or packet_id or "typed controller goal"
    if required_action == CONTINUE_TO_GOAL_ACTION:
        return {
            "user_action": "Continue to the typed goal",
            "continuation_goal": goal,
            "why_not_done": (
                "A scoped packet is pending, so final response is denied "
                "until the loop handles that packet's typed goal."
            ),
            "user_continue_state": "must_continue",
        }
    if required_action == "post_continuation_anchor":
        return {
            "user_action": "Post continuation anchor before stopping",
            "continuation_goal": goal,
            "why_not_done": (
                "The termination policy requires a scoped continuation anchor "
                "before this session can close."
            ),
            "user_continue_state": "must_continue",
        }
    if required_action == "continue_from_continuation_anchor":
        return {
            "user_action": "Continue from live continuation anchor",
            "continuation_goal": goal,
            "why_not_done": (
                "A scoped continuation anchor is active, so the session must "
                "keep working until a matching stop anchor or closure proof exists."
            ),
            "user_continue_state": "must_continue",
        }
    if should_continue_loop:
        return {
            "user_action": "Continue loop",
            "continuation_goal": goal,
            "why_not_done": reason or next_command or "Typed controller still has work.",
            "user_continue_state": "must_continue",
        }
    return {
        "user_action": required_action,
        "continuation_goal": goal if required_action != "stop_no_work" else "",
        "why_not_done": "" if required_action == "stop_no_work" else reason,
        "user_continue_state": "may_stop" if required_action == "stop_no_work" else "must_continue",
    }


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
    "packet_attention_pending_decision",
    "pending_review_packet_decision",
    "session_identity_decision",
    "next_command_for_turn",
    "unresolved_decision",
    "wait_decision",
]
