"""Builder helpers for the compact authority snapshot contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .action_routing import build_startup_action_routing
from .advisory_next_action_role_filter import project_next_command_for_role
from .authority_snapshot_actions import (
    AuthorityActionInputs,
    authority_actions,
    authority_modes,
    reviewer_provider_from_payload,
)
from .authority_snapshot_actor import (
    authority_actor_identity,
    authority_actor_role,
)
from .authority_snapshot_core import (
    AuthoritySnapshot,
    _coordination_state,
    _mapping,
    _safe_to_continue,
    _string_items,
    summary_next_command,
)
from .authority_snapshot_packet_target import select_packet_target
from .authority_snapshot_provenance import authority_snapshot_provenance_kwargs
from .authority_snapshot_instructions import (
    AuthorityInstructionInputs,
    current_instruction_for_reviewer,
    instruction_requires_clear,
    resolved_coordination_current_slice,
)
from .review_state_semantics import is_missing_instruction


@dataclass(frozen=True, slots=True)
class AuthorityBuildContext:
    payload: Mapping[str, object]
    recovery_authority: Mapping[str, object]
    attention: Mapping[str, object]
    doctor: Mapping[str, object]
    recovery: Mapping[str, object]
    diagnosis: Mapping[str, object]
    decision: Mapping[str, object]
    coordination: Mapping[str, object]
    current_session: Mapping[str, object]
    reviewer_gate: Mapping[str, object]
    reviewer_runtime: Mapping[str, object]
    packet_inbox: Mapping[str, object]
    packet_target: object
    reviewer_agent: str


def _build_authority_context(payload: Mapping[str, object]) -> AuthorityBuildContext:
    recovery_authority = _mapping(payload.get("recovery_authority"))
    attention = _mapping(payload.get("attention"))
    doctor = _mapping(payload.get("doctor"))
    recovery = _mapping(payload.get("recovery_assessment"))
    diagnosis = _mapping(recovery.get("diagnosis"))
    decision = _mapping(recovery.get("decision"))
    coordination = _mapping(payload.get("coordination"))
    current_session = _mapping(payload.get("current_session"))
    reviewer_gate = _mapping(payload.get("reviewer_gate"))
    reviewer_runtime = _mapping(payload.get("reviewer_runtime"))
    packet_inbox = _mapping(payload.get("packet_inbox"))
    return AuthorityBuildContext(
        payload=payload,
        recovery_authority=recovery_authority,
        attention=attention,
        doctor=doctor,
        recovery=recovery,
        diagnosis=diagnosis,
        decision=decision,
        coordination=coordination,
        current_session=current_session,
        reviewer_gate=reviewer_gate,
        reviewer_runtime=reviewer_runtime,
        packet_inbox=packet_inbox,
        packet_target=select_packet_target(packet_inbox),
        reviewer_agent=reviewer_provider_from_payload(payload),
    )


def _resolved_next_command(
    *,
    payload: Mapping[str, object],
    recovery_authority: Mapping[str, object],
    doctor: Mapping[str, object],
    decision: Mapping[str, object],
    next_command: str,
) -> str:
    command = (
        next_command
        or str(recovery_authority.get("command") or "").strip()
        or str(payload.get("next_command") or "").strip()
        or str(doctor.get("decision_command") or "").strip()
        or str(decision.get("command") or "").strip()
        or str(payload.get("recommended_command") or "").strip()
    )
    if command:
        return command
    if (
        "reviewer_gate" in payload
        or "implementation_permission" in payload
        or "push_decision" in payload
    ):
        return summary_next_command(payload)
    return ""


def _resolved_action_sets(
    *,
    payload: Mapping[str, object],
    command: str,
    caller_role: object,
    reviewer_override: bool,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    allowed_actions = _string_items(payload.get("allowed_actions"))
    blocked_actions = _string_items(payload.get("blocked_actions"))
    if allowed_actions or blocked_actions:
        return allowed_actions, blocked_actions
    if not (
        "coordination" in payload
        or "implementation_permission" in payload
        or "reviewer_gate" in payload
        or "work_intake" in payload
        or "governance" in payload
    ):
        return allowed_actions, blocked_actions
    routing = build_startup_action_routing(
        payload,
        next_command=command,
        caller_role=caller_role,
        reviewer_override=reviewer_override,
    )
    return routing.allowed_actions, routing.blocked_actions


def build_authority_snapshot(
    payload: Mapping[str, object],
    *,
    next_command: str = "",
    caller_role: object = "",
    reviewer_override: bool = False,
) -> AuthoritySnapshot:
    """Reduce a startup/session/status payload into one compact authority object."""
    context = _build_authority_context(payload)
    collaboration = _mapping(payload.get("collaboration"))
    command = _resolved_next_command(
        payload=payload,
        recovery_authority=context.recovery_authority,
        doctor=context.doctor,
        decision=context.decision,
        next_command=next_command,
    )
    command = project_next_command_for_role(role=caller_role, command=command)
    allowed_actions, blocked_actions = _resolved_action_sets(
        payload=payload,
        command=command,
        caller_role=caller_role,
        reviewer_override=reviewer_override,
    )
    actor_role = authority_actor_role(payload=payload, caller_role=caller_role)
    actor_identity = authority_actor_identity(
        coordination=context.coordination,
        actor_role=actor_role,
    )
    current_instruction = str(
        context.current_session.get("current_instruction") or ""
    ).strip()
    clear_from_packet_truth = instruction_requires_clear(
        AuthorityInstructionInputs(
            packet_inbox=context.packet_inbox,
            packet_target=context.packet_target,
            reviewer_agent=context.reviewer_agent,
            actor_role=actor_role,
            actor_identity=actor_identity,
            coordination_has_actors=isinstance(context.coordination.get("actors"), list)
            and bool(context.coordination.get("actors")),
            current_instruction=current_instruction,
            coordination_current_slice=str(
                context.coordination.get("current_slice") or ""
            ).strip(),
        )
    )
    reviewer_mode, reviewer_freshness, attention_status = authority_modes(
        payload=payload,
        reviewer_gate=context.reviewer_gate,
        reviewer_runtime=context.reviewer_runtime,
        diagnosis=context.diagnosis,
        attention=context.attention,
        doctor=context.doctor,
    )
    implementation_permission = str(
        payload.get("implementation_permission")
        or _mapping(_mapping(payload.get("work_intake")).get("coordination")).get(
            "implementation_permission"
        )
        or ("blocked" if bool(context.doctor.get("implementation_blocked", False)) else "")
        or ""
    ).strip()
    resync_required = bool(context.coordination.get("resync_required", False))
    current_instruction_revision = (
        ""
        if clear_from_packet_truth or is_missing_instruction(current_instruction)
        else str(context.current_session.get("current_instruction_revision") or "").strip()
    )
    implementer_ack_state = (
        "missing"
        if clear_from_packet_truth or is_missing_instruction(current_instruction)
        else str(context.current_session.get("implementer_ack_state") or "").strip()
    )
    root_cause, required_action = authority_actions(
        AuthorityActionInputs(
            payload=payload,
            reviewer_gate=context.reviewer_gate,
            attention=context.attention,
            doctor=context.doctor,
            diagnosis=context.diagnosis,
            decision=context.decision,
            recovery_authority=context.recovery_authority,
        )
    )
    coordination_state = _coordination_state(
        (
            reviewer_mode,
            attention_status,
            implementation_permission,
            resync_required,
            current_instruction_revision,
            implementer_ack_state,
            root_cause,
        )
    )
    safe_to_continue = _safe_to_continue(
        coordination_state=coordination_state,
        implementation_permission=implementation_permission,
        allowed_actions=allowed_actions,
    )
    active_target = _mapping(context.coordination.get("active_target"))
    current_instruction = current_instruction_for_reviewer(
        current_session=context.current_session,
        clear_from_packet_truth=clear_from_packet_truth,
    )
    coordination_current_slice = resolved_coordination_current_slice(
        coordination=context.coordination,
        current_session=context.current_session,
        clear_from_packet_truth=clear_from_packet_truth,
    )
    return AuthoritySnapshot(
        **authority_snapshot_provenance_kwargs(payload),
        coordination_state=coordination_state,
        root_cause=root_cause,
        required_action=required_action,
        next_command=command,
        actor_role=actor_role,
        actor_identity=actor_identity,
        safe_to_continue=safe_to_continue,
        reviewer_mode=reviewer_mode,
        reviewer_freshness=reviewer_freshness,
        attention_status=attention_status,
        observed_control_topology=str(
            payload.get("observed_control_topology")
            or context.coordination.get("observed_topology")
            or ""
        ).strip(),
        implementation_permission=implementation_permission,
        current_instruction_revision=current_instruction_revision,
        implementer_ack_state=implementer_ack_state,
        resync_required=resync_required,
        current_slice=str(coordination_current_slice or current_instruction or "").strip(),
        active_target_path=str(active_target.get("plan_path") or "").strip(),
        allowed_actions=allowed_actions,
        blocked_actions=blocked_actions,
        packet_target=context.packet_target,
        mutation_owner=str(collaboration.get("mutation_owner") or "").strip(),
        verification_owner=str(collaboration.get("verification_owner") or "").strip(),
        verification_status=str(
            collaboration.get("verification_status") or "inactive"
        ).strip(),
        watcher_owner=str(collaboration.get("watcher_owner") or "").strip(),
        watcher_status=str(collaboration.get("watcher_status") or "inactive").strip(),
    )


def project_authority_snapshot(
    payload: dict[str, object],
    *,
    next_command: str = "",
    caller_role: object = "",
    reviewer_override: bool = False,
) -> AuthoritySnapshot:
    """Attach an authority snapshot to an existing payload."""
    snapshot = build_authority_snapshot(
        payload,
        next_command=next_command,
        caller_role=caller_role,
        reviewer_override=reviewer_override,
    )
    payload["authority_snapshot"] = snapshot.to_dict()
    return snapshot
