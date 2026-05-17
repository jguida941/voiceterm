"""AgentLoopDecision assembly helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from .agent_loop_command import scoped_loop_command, scoped_operator_override_command
from .agent_loop_decision_models import AgentLoopDecision
from .agent_loop_decision_sources import AgentLoopContext, PacketState
from .agent_loop_policy import policy_for_turn
from .typed_gate_failure import TypedGateFailure
from .value_coercion import coerce_bool, coerce_int, coerce_text as _text

CONTINUE_TO_GOAL_ACTION = "continue_to_goal"
SCOPED_IMPLEMENTATION_EDIT_ACTION = "continue_scoped_implementation_edit"


def decision(
    ctx: AgentLoopContext,
    loop_state: str,
    required_action: str,
    reason: str,
    **overrides: object,
) -> AgentLoopDecision:
    lifecycle_state = _text(overrides.get("lifecycle_state"))
    decision_code = _text(overrides.get("decision_code"))
    reason_code = _text(overrides.get("reason_code"))
    should_continue_loop = coerce_bool(overrides.get("should_continue_loop"))
    safe_to_continue = coerce_bool(overrides.get("safe_to_continue"))
    may_mutate = coerce_bool(overrides.get("may_mutate"))
    active_packet_id = _text(overrides.get("active_packet_id"))
    attention_packet_id = _text(overrides.get("attention_packet_id"))
    executing_packet_id = _text(overrides.get("executing_packet_id"))
    legacy_unscoped_packet_id = _text(overrides.get("legacy_unscoped_packet_id"))
    plan_target_ref = _text(overrides.get("plan_target_ref"))
    next_command_override = _text(overrides.get("next_command_override"))
    resolved_lifecycle = lifecycle_from_loop_state(loop_state)
    resolved_decision = decision_code or decision_from_loop_state(loop_state)
    command_ctx = _command_context_for_turn(
        ctx,
        active_packet_id=active_packet_id,
        attention_packet_id=attention_packet_id,
        executing_packet_id=executing_packet_id,
    )
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
        and required_action
        in {"repair_startup_authority", SCOPED_IMPLEMENTATION_EDIT_ACTION}
    )
    next_command = next_command_for_turn(
        ctx=command_ctx,
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
    gate_failure = _gate_failure_for_decision(
        loop_state=loop_state,
        required_action=required_action,
        reason=reason,
        next_command=next_command,
        should_continue_loop=effective_should_continue_loop,
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
        lifecycle_state=lifecycle_state or resolved_lifecycle,
        decision=resolved_decision,
        reason_code=reason_code or required_action,
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
        body_open_required=coerce_bool(ctx.attention.get("body_open_required")),
        body_open_packet_id=_text(ctx.attention.get("body_open_packet_id")),
        semantic_ingestion_required=coerce_bool(
            ctx.attention.get("semantic_ingestion_required")
        ),
        semantic_ingestion_packet_id=_text(
            ctx.attention.get("semantic_ingestion_packet_id")
        ),
        semantic_ingestion_reason=_text(ctx.attention.get("semantic_ingestion_reason")),
        allowed_actions=ctx.allowed_actions,
        blocked_actions=ctx.blocked_actions,
        granted_capabilities=ctx.granted_capabilities,
        operator_override=ctx.operator_override,
        gate_failure=gate_failure,
        source_latest_event_id=_text(ctx.clock.get("source_latest_event_id")),
        source_snapshot_id=_text(ctx.clock.get("snapshot_id")),
    )


def _gate_failure_for_decision(
    *,
    loop_state: str,
    required_action: str,
    reason: str,
    next_command: str,
    should_continue_loop: bool,
) -> TypedGateFailure | None:
    if not should_continue_loop:
        return None
    gate_id = _gate_id_for_decision(loop_state=loop_state, required_action=required_action)
    if not gate_id:
        return None
    return TypedGateFailure(
        gate_id=gate_id,
        violation_reason=reason or required_action,
        bypass_invocation=(
            next_command if "--operator-override" in next_command else ""
        ),
        contract_definition_path=_gate_contract_path(required_action),
    )


def _gate_id_for_decision(*, loop_state: str, required_action: str) -> str:
    if required_action in {
        "repair_startup_authority",
        "resolve_blocker",
        "cut_checkpoint",
        "wait_for_review",
        "wait_for_scoped_packet",
    }:
        return f"agent_loop.{required_action}"
    if loop_state == "blocked" and required_action:
        return f"agent_loop.{required_action}"
    return ""


def _gate_contract_path(required_action: str) -> str:
    if required_action == "repair_startup_authority":
        return "dev/scripts/devctl/runtime/startup_blocker_decision.py:126"
    if required_action == "cut_checkpoint":
        return "dev/scripts/devctl/runtime/checkpoint_repair_authority.py:1"
    if required_action == "wait_for_scoped_packet":
        return "dev/scripts/devctl/runtime/agent_loop_decision_support.py:306"
    if required_action == "wait_for_review":
        return "dev/scripts/devctl/runtime/agent_loop_blocker_actions.py:17"
    return "dev/scripts/devctl/runtime/agent_loop_decision_builder.py:1"


def _command_context_for_turn(
    ctx: AgentLoopContext,
    *,
    active_packet_id: str,
    attention_packet_id: str,
    executing_packet_id: str,
) -> AgentLoopContext:
    if not ctx.requested_packet_id:
        return ctx
    if active_packet_id or attention_packet_id or executing_packet_id:
        return ctx
    return replace(ctx, requested_packet_id="")


def lifecycle_from_loop_state(loop_state: str) -> str:
    lifecycle_by_loop_state = {
        "blocked": "blocked",
        "work": "needs_attention",
        "observe": "idle",
        "wait": "waiting",
        "done": "completed",
    }
    return lifecycle_by_loop_state.get(loop_state, "blocked")


def next_command_for_turn(
    *,
    ctx: object,
    loop_policy: object,
    loop_state: str,
    required_action: str,
    should_continue_loop: bool,
    reason: str,
    **options: object,
) -> str:
    """Return the command a simple loop driver should run next."""
    next_command_override = _text(options.get("next_command_override"))
    override_request_next = scoped_operator_override_command(ctx, reason=reason)
    loop_next_command = scoped_loop_command(ctx)
    if next_command_override:
        return next_command_override
    if (
        ctx.operator_override.edit_allowed
        and required_action
        in {
            "repair_startup_authority",
            "governed_checkpoint_commit",
            SCOPED_IMPLEMENTATION_EDIT_ACTION,
        }
    ):
        return ""
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
            and loop_next_command
        ):
            return loop_next_command
        return ""
    if loop_policy.can_run_next_command:
        return ctx.next_command
    if should_continue_loop and loop_next_command:
        return loop_next_command
    return ""


def decision_from_loop_state(loop_state: str) -> str:
    decision_by_loop_state = {
        "blocked": "run_next_command",
        "work": CONTINUE_TO_GOAL_ACTION,
        "observe": "wait",
        "wait": "wait",
        "done": "stop_no_work",
    }
    return decision_by_loop_state.get(loop_state, "run_next_command")


def attention_reason(ctx: AgentLoopContext) -> str:
    reason = _text(ctx.attention.get("stale_reason"))
    if reason == "wake_required":
        return "peer_input_required"
    if reason == "actor_identity_ambiguous_with_pending_wake":
        return "actor_identity_ambiguous_with_pending_peer_input"
    return reason


def body_open_required(ctx: AgentLoopContext) -> bool:
    value = ctx.attention.get("body_open_required")
    return coerce_bool(value)


def body_open_command(ctx: AgentLoopContext) -> str:
    value = ctx.attention.get("body_open_command")
    return _text(value)


def semantic_ingestion_required(ctx: AgentLoopContext) -> bool:
    return coerce_bool(ctx.attention.get("semantic_ingestion_required"))


def semantic_ingestion_command(ctx: AgentLoopContext) -> str:
    return _text(ctx.attention.get("semantic_ingestion_command"))


def body_open_decision(
    ctx: AgentLoopContext,
    packets: PacketState,
    pivot_packet_id: str,
    pivot_packet: Mapping[str, object],
    *,
    next_command_override: str = "",
) -> AgentLoopDecision:
    packet_id = _text(ctx.attention.get("body_open_packet_id")) or pivot_packet_id
    semantic_required = semantic_ingestion_required(ctx)
    required_action = (
        "ingest_packet_semantics" if semantic_required else "open_packet_body"
    )
    reason_code = (
        "packet_semantic_ingestion_required"
        if semantic_required
        else "packet_body_open_required"
    )
    return decision(
        ctx,
        "blocked",
        required_action,
        attention_reason(ctx) or reason_code,
        lifecycle_state="needs_attention",
        decision_code="run_next_command",
        reason_code=reason_code,
        should_continue_loop=True,
        safe_to_continue=False,
        may_mutate=False,
        active_packet_id=packet_id,
        attention_packet_id=packet_id or packets.attention_packet_id,
        executing_packet_id=packets.executing_packet_id,
        legacy_unscoped_packet_id=packets.legacy_unscoped_packet_id,
        plan_target_ref=_text(pivot_packet.get("target_ref")),
        next_command_override=(
            next_command_override
            or semantic_ingestion_command(ctx)
            or body_open_command(ctx)
        ),
    )


def readable_decision_fields(
    *,
    required_action: str,
    reason: str,
    active_packet_id: str,
    attention_packet_id: str,
    plan_target_ref: str,
    **state: object,
) -> dict[str, str]:
    should_continue_loop = coerce_bool(state.get("should_continue_loop"))
    next_command = _text(state.get("next_command"))
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
    if required_action == SCOPED_IMPLEMENTATION_EDIT_ACTION:
        return {
            "user_action": "Continue scoped implementation edits",
            "continuation_goal": goal,
            "why_not_done": (
                "An edit-only operator override is active for this plan target; "
                "implementation edits may continue while staging, commit, and "
                "push remain blocked."
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
        "user_continue_state": "may_stop"
        if required_action == "stop_no_work"
        else "must_continue",
    }
