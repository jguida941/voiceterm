"""Builder helpers for the compact authority snapshot contract."""

from __future__ import annotations

from collections.abc import Mapping

from .action_routing import build_startup_action_routing
from .authority_snapshot_core import (
    AuthoritySnapshot,
    _coordination_state,
    _mapping,
    _safe_to_continue,
    _select_packet_target,
    _string_items,
    summary_next_command,
)


def build_authority_snapshot(
    payload: Mapping[str, object],
    *,
    next_command: str = "",
    caller_role: object = "",
    reviewer_override: bool = False,
) -> AuthoritySnapshot:
    """Reduce a startup/session/status payload into one compact authority object."""
    recovery_authority = _mapping(payload.get("recovery_authority"))
    command = (
        next_command
        or str(recovery_authority.get("command") or "").strip()
        or str(payload.get("next_command") or "").strip()
    )
    if not command and (
        "reviewer_gate" in payload
        or "implementation_permission" in payload
        or "push_decision" in payload
    ):
        command = summary_next_command(payload)

    allowed_actions = _string_items(payload.get("allowed_actions"))
    blocked_actions = _string_items(payload.get("blocked_actions"))
    if not allowed_actions and not blocked_actions and (
        "reviewer_gate" in payload or "work_intake" in payload or "governance" in payload
    ):
        routing = build_startup_action_routing(
            payload,
            next_command=command,
            caller_role=caller_role,
            reviewer_override=reviewer_override,
        )
        allowed_actions = routing.allowed_actions
        blocked_actions = routing.blocked_actions

    coordination = _mapping(payload.get("coordination"))
    current_session = _mapping(payload.get("current_session"))
    reviewer_gate = _mapping(payload.get("reviewer_gate"))
    reviewer_runtime = _mapping(payload.get("reviewer_runtime"))
    attention = _mapping(payload.get("attention"))
    doctor = _mapping(payload.get("doctor"))
    recovery = _mapping(payload.get("recovery_assessment"))
    diagnosis = _mapping(recovery.get("diagnosis"))
    decision = _mapping(recovery.get("decision"))
    packet_inbox = _mapping(payload.get("packet_inbox"))

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
    implementation_permission = str(
        payload.get("implementation_permission")
        or _mapping(_mapping(payload.get("work_intake")).get("coordination")).get(
            "implementation_permission"
        )
        or ("blocked" if bool(doctor.get("implementation_blocked", False)) else "")
        or ""
    ).strip()
    resync_required = bool(coordination.get("resync_required", False))
    current_instruction_revision = str(
        current_session.get("current_instruction_revision") or ""
    ).strip()
    implementer_ack_state = str(
        current_session.get("implementer_ack_state") or ""
    ).strip()
    root_cause = (
        str(doctor.get("root_cause") or "").strip()
        or str(diagnosis.get("root_cause") or "").strip()
        or str(doctor.get("summary") or "").strip()
        or str(attention.get("summary") or "").strip()
        or str(payload.get("advisory_reason") or "").strip()
        or str(reviewer_gate.get("implementation_block_reason") or "").strip()
    )
    required_action = (
        str(doctor.get("decision_action_id") or "").strip()
        or str(decision.get("action_id") or "").strip()
        or str(recovery_authority.get("decision_action_id") or "").strip()
        or str(doctor.get("recovery_action_allowed") or "").strip()
        or str(payload.get("control_recovery_action") or "").strip()
        or str(payload.get("advisory_action") or "").strip()
        or str(attention.get("recommended_action") or "").strip()
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

    active_target = _mapping(coordination.get("active_target"))
    return AuthoritySnapshot(
        coordination_state=coordination_state,
        root_cause=root_cause,
        required_action=required_action,
        next_command=command,
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
            coordination.get("current_slice")
            or current_session.get("current_instruction")
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
