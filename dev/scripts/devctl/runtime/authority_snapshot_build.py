"""Builder helpers for the compact authority snapshot contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .action_routing import build_startup_action_routing
from .authority_snapshot_actor import (
    authority_actor_identity,
    authority_actor_role,
)
from .authority_snapshot_core import (
    AuthoritySnapshot,
    _coordination_state,
    _mapping,
    _safe_to_continue,
    _select_packet_target,
    _string_items,
    summary_next_command,
)
from .review_state_semantics import is_missing_instruction


@dataclass(frozen=True, slots=True)
class AuthorityActionInputs:
    payload: Mapping[str, object]
    reviewer_gate: Mapping[str, object]
    attention: Mapping[str, object]
    doctor: Mapping[str, object]
    diagnosis: Mapping[str, object]
    decision: Mapping[str, object]
    recovery_authority: Mapping[str, object]


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
    recovery_authority = _mapping(payload.get("recovery_authority"))
    attention = _mapping(payload.get("attention"))
    doctor = _mapping(payload.get("doctor"))
    recovery = _mapping(payload.get("recovery_assessment"))
    diagnosis = _mapping(recovery.get("diagnosis"))
    decision = _mapping(recovery.get("decision"))
    command = _resolved_next_command(
        payload=payload,
        recovery_authority=recovery_authority,
        doctor=doctor,
        decision=decision,
        next_command=next_command,
    )
    allowed_actions, blocked_actions = _resolved_action_sets(
        payload=payload,
        command=command,
        caller_role=caller_role,
        reviewer_override=reviewer_override,
    )

    coordination = _mapping(payload.get("coordination"))
    current_session = _mapping(payload.get("current_session"))
    reviewer_gate = _mapping(payload.get("reviewer_gate"))
    reviewer_runtime = _mapping(payload.get("reviewer_runtime"))
    packet_inbox = _mapping(payload.get("packet_inbox"))
    current_instruction = str(current_session.get("current_instruction") or "").strip()
    clear_from_packet_truth = _codex_instruction_requires_clear(packet_inbox)
    reviewer_mode, reviewer_freshness, attention_status = _authority_modes(
        payload=payload,
        reviewer_gate=reviewer_gate,
        reviewer_runtime=reviewer_runtime,
        diagnosis=diagnosis,
        attention=attention,
        doctor=doctor,
    )
    implementation_permission = str(
        payload.get("implementation_permission")
        or _mapping(_mapping(payload.get("work_intake")).get("coordination")).get(
            "implementation_permission"
        )
        or ("blocked" if bool(doctor.get("implementation_blocked", False)) else "")
        or ""
    ).strip()
    resync_required = bool(coordination.get("resync_required", False))
    current_instruction_revision = (
        ""
        if clear_from_packet_truth or is_missing_instruction(current_instruction)
        else str(current_session.get("current_instruction_revision") or "").strip()
    )
    implementer_ack_state = (
        "missing"
        if clear_from_packet_truth or is_missing_instruction(current_instruction)
        else str(current_session.get("implementer_ack_state") or "").strip()
    )
    root_cause, required_action = _authority_actions(
        AuthorityActionInputs(
            payload=payload,
            reviewer_gate=reviewer_gate,
            attention=attention,
            doctor=doctor,
            diagnosis=diagnosis,
            decision=decision,
            recovery_authority=recovery_authority,
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
    actor_role = authority_actor_role(payload=payload, caller_role=caller_role)
    actor_identity = authority_actor_identity(
        coordination=coordination,
        actor_role=actor_role,
    )

    active_target = _mapping(coordination.get("active_target"))
    current_instruction = _current_instruction_for_reviewer(
        current_session=current_session,
        packet_inbox=packet_inbox,
    )
    coordination_current_slice = _resolved_coordination_current_slice(
        coordination=coordination,
        current_session=current_session,
        packet_inbox=packet_inbox,
    )
    return AuthoritySnapshot(
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
            or coordination.get("observed_topology")
            or ""
        ).strip(),
        implementation_permission=implementation_permission,
        current_instruction_revision=current_instruction_revision,
        implementer_ack_state=implementer_ack_state,
        resync_required=resync_required,
        current_slice=str(
            coordination_current_slice
            or current_instruction
            or ""
        ).strip(),
        active_target_path=str(active_target.get("plan_path") or "").strip(),
        allowed_actions=allowed_actions,
        blocked_actions=blocked_actions,
        packet_target=_select_packet_target(packet_inbox),
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


def _current_instruction_for_reviewer(
    *,
    current_session: Mapping[str, object],
    packet_inbox: Mapping[str, object],
) -> str:
    instruction = str(current_session.get("current_instruction") or "").strip()
    if _codex_instruction_requires_clear(packet_inbox) or is_missing_instruction(
        instruction
    ):
        return ""
    return instruction


def _resolved_coordination_current_slice(
    *,
    coordination: Mapping[str, object],
    current_session: Mapping[str, object],
    packet_inbox: Mapping[str, object],
) -> str:
    current_slice = str(coordination.get("current_slice") or "").strip()
    raw_current_instruction = str(current_session.get("current_instruction") or "").strip()
    if _codex_instruction_requires_clear(packet_inbox) and current_slice == raw_current_instruction:
        return ""
    if is_missing_instruction(raw_current_instruction) and current_slice == raw_current_instruction:
        return ""
    return current_slice


def _authority_modes(
    *,
    payload: Mapping[str, object],
    reviewer_gate: Mapping[str, object],
    reviewer_runtime: Mapping[str, object],
    diagnosis: Mapping[str, object],
    attention: Mapping[str, object],
    doctor: Mapping[str, object],
) -> tuple[str, str, str]:
    reviewer_mode = (
        str(reviewer_gate.get("effective_reviewer_mode") or "").strip()
        or str(reviewer_gate.get("reviewer_mode") or "").strip()
        or str(reviewer_runtime.get("effective_reviewer_mode") or "").strip()
        or str(reviewer_runtime.get("reviewer_mode") or "").strip()
        or str(payload.get("reviewer_mode") or "").strip()
    )
    reviewer_freshness = (
        str(reviewer_runtime.get("reviewer_freshness") or "").strip()
        or str(payload.get("reviewer_freshness") or "").strip()
        or str(payload.get("codex_poll_state") or "").strip()
    )
    attention_status = (
        str(diagnosis.get("status") or "").strip()
        or str(attention.get("status") or "").strip()
        or str(doctor.get("status") or "").strip()
    )
    return reviewer_mode, reviewer_freshness, attention_status


def _authority_actions(inputs: AuthorityActionInputs) -> tuple[str, str]:
    root_cause = (
        str(inputs.doctor.get("root_cause") or "").strip()
        or str(inputs.diagnosis.get("root_cause") or "").strip()
        or str(inputs.doctor.get("summary") or "").strip()
        or str(inputs.attention.get("summary") or "").strip()
        or str(inputs.payload.get("advisory_reason") or "").strip()
        or str(inputs.reviewer_gate.get("implementation_block_reason") or "").strip()
    )
    required_action = (
        str(inputs.doctor.get("decision_action_id") or "").strip()
        or str(inputs.decision.get("action_id") or "").strip()
        or str(inputs.recovery_authority.get("decision_action_id") or "").strip()
        or str(inputs.doctor.get("recovery_action_allowed") or "").strip()
        or str(inputs.payload.get("control_recovery_action") or "").strip()
        or str(inputs.payload.get("advisory_action") or "").strip()
        or str(inputs.attention.get("recommended_action") or "").strip()
    )
    return root_cause, required_action


def _codex_instruction_requires_clear(packet_inbox: Mapping[str, object]) -> bool:
    agents = packet_inbox.get("agents")
    if not isinstance(agents, list):
        return False
    record = next(
        (
            _mapping(row)
            for row in agents
            if str(_mapping(row).get("agent") or "").strip().lower() == "codex"
        ),
        {},
    )
    if not record:
        return False
    return not str(record.get("current_instruction_packet_id") or "").strip()
