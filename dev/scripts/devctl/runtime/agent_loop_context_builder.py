"""Builder for AgentLoopContext source snapshots."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from ..review_channel.agent_packet_attention import packet_attention_for_agent
from ..review_channel.packet_contract import normalize_packet_route_role
from .agent_loop_checkpoint_repair import checkpoint_repair_next_action_for_review_state
from .agent_loop_decision_grants import (
    action_routing_decision,
    authority_snapshot,
    granted_capabilities_for_actor,
    lane_edit_allowed,
    may_actor_mutate,
    merged_actions,
    reconcile_actions_with_capability_grants,
    scoped_session_mutation_mode_allows,
)
from .agent_loop_operator_override import (
    apply_operator_override_actions,
    operator_override_from_request,
)
from .value_coercion import coerce_bool
from .value_coercion import coerce_mapping as _mapping
from .value_coercion import coerce_text as _text


@dataclass(frozen=True, slots=True)
class AgentLoopContextBuildInput:
    review_state: Mapping[str, object]
    dashboard: Mapping[str, object]
    actor_id: object
    actor_role: object = ""
    session_id: object = ""
    loop_intent: object = ""
    requested_plan_ref: object = ""
    requested_packet_id: object = ""
    master_plan: object = None
    operator_override_requested: object = False
    operator_override_reason: object = ""
    operator_override_scope: object = "edit-only"
    operator_override_by: object = "operator"


def build_agent_loop_context_impl(inputs: AgentLoopContextBuildInput):
    from .agent_loop_decision_sources import (
        AgentLoopContext,
        current_instruction_revision,
        normalize_loop_intent,
        scoped_packet_attention,
    )

    actor = _text(inputs.actor_id)
    role = normalize_packet_route_role(inputs.actor_role)
    session = _text(inputs.session_id)
    control_plane = _mapping(inputs.dashboard.get("control_plane"))
    now = _mapping(inputs.dashboard.get("now"))
    top_blocker = _text(control_plane.get("top_blocker")) or _text(
        now.get("top_blocker")
    )
    next_action = _text(control_plane.get("next_action")) or _text(
        now.get("next_action")
    )
    next_command = _text(control_plane.get("next_command")) or _text(
        inputs.dashboard.get("next_command")
    )
    next_action, next_command = checkpoint_repair_next_action_for_review_state(
        inputs.review_state,
        top_blocker=top_blocker,
        next_action=next_action,
        next_command=next_command,
    )
    authority = authority_snapshot(
        review_state=inputs.review_state,
        dashboard=inputs.dashboard,
    )
    action_routing = action_routing_decision(
        review_state=inputs.review_state,
        dashboard=inputs.dashboard,
    )
    grants = granted_capabilities_for_actor(
        review_state=inputs.review_state,
        dashboard=inputs.dashboard,
        actor=actor,
        role=role,
        session=session,
    )
    edit_allowed = lane_edit_allowed(
        review_state=inputs.review_state,
        dashboard=inputs.dashboard,
    ) and scoped_session_mutation_mode_allows(
        review_state=inputs.review_state,
        dashboard=inputs.dashboard,
        actor=actor,
        role=role,
        session=session,
    )
    allowed_actions = merged_actions(authority, action_routing, key="allowed_actions")
    blocked_actions = merged_actions(authority, action_routing, key="blocked_actions")
    allowed_actions, blocked_actions = reconcile_actions_with_capability_grants(
        allowed_actions=allowed_actions,
        blocked_actions=blocked_actions,
        granted_capabilities=grants,
    )
    override = operator_override_from_request(
        requested=inputs.operator_override_requested,
        reason=inputs.operator_override_reason,
        scope=inputs.operator_override_scope,
        requested_by=inputs.operator_override_by,
        requested_plan_ref=inputs.requested_plan_ref,
        requested_packet_id=inputs.requested_packet_id,
    )
    allowed_actions, blocked_actions = apply_operator_override_actions(
        allowed_actions=allowed_actions,
        blocked_actions=blocked_actions,
        operator_override=override,
    )
    reviewer_runtime = _mapping(inputs.review_state.get("reviewer_runtime"))
    return AgentLoopContext(
        review_state=inputs.review_state,
        dashboard=inputs.dashboard,
        actor=actor,
        role=role,
        session=session,
        master_plan=_mapping(inputs.master_plan)
        or _mapping(inputs.review_state.get("master_plan")),
        clock=_mapping(reviewer_runtime.get("agent_runtime_clock"))
        or _mapping(inputs.dashboard.get("agent_runtime_clock")),
        attention=asdict(
            packet_attention_for_agent(
                inputs.review_state,
                actor=actor,
                role=role,
                session=session,
                fallback_attention=scoped_packet_attention(
                    review_state=inputs.review_state,
                    dashboard=inputs.dashboard,
                    actor=actor,
                    session=session,
                ),
            )
        ),
        authority=authority,
        action_routing=action_routing,
        allowed_actions=allowed_actions,
        blocked_actions=blocked_actions,
        granted_capabilities=grants,
        operator_override=override,
        may_mutate=override.edit_allowed or may_actor_mutate(
            granted_capabilities=grants,
            allowed_actions=allowed_actions,
            blocked_actions=blocked_actions,
            edit_allowed=edit_allowed,
        ),
        top_blocker=top_blocker,
        next_action=next_action,
        next_command=next_command,
        current_instruction_revision=current_instruction_revision(
            review_state=inputs.review_state,
            dashboard=inputs.dashboard,
        ),
        loop_intent=normalize_loop_intent(inputs.loop_intent),
        requested_plan_ref=_text(inputs.requested_plan_ref),
        requested_packet_id=_text(inputs.requested_packet_id),
        # Phase 0.6.A v4.23 (rev_pkt_4692): read BlockerSnapshot typed action
        # fields from dashboard.control_plane so the decision builder can
        # carry them through to downstream consumers.
        #
        # v4.45 (rev_pkt_4729/4730/4732): normalize so an empty repair_command
        # cannot reach the decision claiming repair_command_runnable=True.
        # The duplicate BlockerSnapshot shape across AgentLoopDecision /
        # AgentLoopContext / ControlPlaneReadModel made it possible for the
        # control plane default (True) to outlive an upstream empty
        # repair_command, producing the contradictory shape codex traced in
        # rev_pkt_4729 (empty repair + repair_command_runnable=True +
        # can_run_next_command=False + self-loop next_command).
        blocker_owner=_text(control_plane.get("blocker_owner")),
        blocker_target=_text(control_plane.get("blocker_target")),
        blocker_reason=_text(control_plane.get("blocker_reason")),
        repair_command=_text(control_plane.get("repair_command")),
        stop_anchor=_text(control_plane.get("stop_anchor")),
        repair_command_runnable=_normalize_repair_command_runnable(
            repair_command=_text(control_plane.get("repair_command")),
            raw_value=control_plane.get("repair_command_runnable", True),
        ),
    )


def _normalize_repair_command_runnable(
    *,
    repair_command: str,
    raw_value: object,
) -> bool:
    """Return the normalized repair_command_runnable flag.

    An empty repair_command can never be runnable. This invariant is enforced
    here so downstream consumers (agent-loop decision builder, final-response
    gate, operator command wrappers, control-decision obedience guard) do not
    have to re-verify it. Prior shape — empty repair_command paired with
    repair_command_runnable=True — was the load-bearing contradiction in the
    rev_pkt_4729 self-loop bug.
    """
    if not repair_command:
        return False
    return coerce_bool(raw_value)
