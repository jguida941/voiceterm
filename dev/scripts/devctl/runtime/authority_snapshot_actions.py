"""Action and reviewer-mode helpers extracted from authority snapshot assembly."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .authority_snapshot_core import _mapping
from .operator_context import is_resolved, resolve_operator_interaction_mode
from .remote_control_attachment_models import (
    has_active_remote_control_attachment,
    remote_control_attachment_from_mapping,
)
from .reviewer_mode import reviewer_mode_is_active, reviewer_mode_is_single_agent


@dataclass(frozen=True, slots=True)
class AuthorityActionInputs:
    payload: Mapping[str, object]
    reviewer_gate: Mapping[str, object]
    attention: Mapping[str, object]
    doctor: Mapping[str, object]
    diagnosis: Mapping[str, object]
    decision: Mapping[str, object]
    recovery_authority: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class AuthorityModeProjection:
    """Canonical reviewer/operator mode projection for runtime authority."""

    reviewer_mode: str = ""
    effective_reviewer_mode: str = ""
    reviewer_freshness: str = ""
    attention_status: str = ""
    interaction_mode: str = "unresolved"
    gate_mode: str = ""
    declared_active: bool = False
    effective_active: bool = False


@dataclass(frozen=True, slots=True)
class AuthorityModeInputs:
    payload: Mapping[str, object]
    reviewer_gate: Mapping[str, object]
    reviewer_runtime: Mapping[str, object]
    diagnosis: Mapping[str, object]
    attention: Mapping[str, object]
    doctor: Mapping[str, object]
    governance_mode: str = ""


def authority_modes(
    *,
    payload: Mapping[str, object],
    reviewer_gate: Mapping[str, object],
    reviewer_runtime: Mapping[str, object],
    diagnosis: Mapping[str, object],
    attention: Mapping[str, object],
    doctor: Mapping[str, object],
) -> tuple[str, str, str]:
    projection = authority_mode_projection(
        AuthorityModeInputs(
            payload=payload,
            reviewer_gate=reviewer_gate,
            reviewer_runtime=reviewer_runtime,
            diagnosis=diagnosis,
            attention=attention,
            doctor=doctor,
        )
    )
    return (
        projection.gate_mode or projection.reviewer_mode,
        projection.reviewer_freshness,
        projection.attention_status,
    )


def authority_mode_projection(inputs: AuthorityModeInputs) -> AuthorityModeProjection:
    """Project all mode/gate fields from one canonical reducer."""
    from .conductor_capability import authority_reviewer_mode

    payload = inputs.payload
    reviewer_gate = inputs.reviewer_gate
    reviewer_runtime = inputs.reviewer_runtime
    diagnosis = inputs.diagnosis
    attention = inputs.attention
    doctor = inputs.doctor
    reviewer_mode = (
        _text(reviewer_runtime.get("reviewer_mode"))
        or _text(reviewer_gate.get("reviewer_mode"))
        or _text(payload.get("reviewer_mode"))
    )
    effective_reviewer_mode = (
        _text(reviewer_runtime.get("effective_reviewer_mode"))
        or _text(reviewer_gate.get("effective_reviewer_mode"))
        or reviewer_mode
    )
    posture = _mapping(payload.get("session_posture")) or _mapping(
        reviewer_runtime.get("session_posture")
    )
    if _posture_has_runtime_truth(posture):
        reviewer_mode = _text(posture.get("reviewer_mode")) or reviewer_mode
        effective_reviewer_mode = (
            _text(posture.get("effective_reviewer_mode")) or effective_reviewer_mode
        )
    interaction_mode = interaction_mode_from_reviewer_mode(
        effective_reviewer_mode,
        governance_mode=inputs.governance_mode or _governance_mode(payload),
        payload=payload,
        reviewer_runtime=reviewer_runtime,
    )
    posture_interaction_mode = _text(posture.get("interaction_mode"))
    if posture_interaction_mode and posture_interaction_mode != "unresolved":
        interaction_mode = posture_interaction_mode
    declared_active = reviewer_mode_is_active(reviewer_mode)
    effective_active = reviewer_mode_is_active(effective_reviewer_mode)
    gate_mode = (
        authority_reviewer_mode(reviewer_mode, effective_reviewer_mode)
        if reviewer_mode or effective_reviewer_mode
        else ""
    )
    return AuthorityModeProjection(
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        reviewer_freshness=(
            _text(reviewer_runtime.get("reviewer_freshness"))
            or _text(payload.get("reviewer_freshness"))
            or _text(payload.get("codex_poll_state"))
        ),
        attention_status=(
            _text(diagnosis.get("status"))
            or _text(attention.get("status"))
            or _text(doctor.get("status"))
        ),
        interaction_mode=interaction_mode,
        gate_mode=gate_mode,
        declared_active=declared_active,
        effective_active=effective_active,
    )


def interaction_mode_from_reviewer_mode(
    effective_mode: str,
    *,
    governance_mode: str = "",
    remote_control_attachment: object | None = None,
    payload: Mapping[str, object] | None = None,
    reviewer_runtime: Mapping[str, object] | None = None,
) -> str:
    """Derive operator interaction mode; fails closed to ``unresolved``."""
    runtime = reviewer_runtime or {}
    attachment = (
        remote_control_attachment
        or remote_control_attachment_from_mapping(runtime.get("remote_control_attachment"))
        or remote_control_attachment_from_mapping(
            _mapping(payload.get("remote_control_attachment")) if payload else {}
        )
    )
    attachment_active = has_active_remote_control_attachment(attachment)
    candidates = (
        governance_mode,
        _text(
            _mapping((payload or {}).get("collaboration")).get(
                "operator_interaction_mode"
            )
        ),
        _text(runtime.get("operator_interaction_mode")),
    )
    saw_local_terminal = False
    for candidate in candidates:
        resolved = resolve_operator_interaction_mode(candidate)
        if resolved.value == "remote_control" and not attachment_active:
            continue
        if (
            is_resolved(resolved.value)
            and resolved.value not in {"local_terminal", "remote_control"}
        ):
            return resolved.value
        if resolved.value == "remote_control" and attachment_active:
            return "remote_control"
        if resolved.value == "local_terminal":
            saw_local_terminal = True
    if attachment_active:
        return "remote_control"
    if saw_local_terminal:
        return "local_terminal"
    if reviewer_mode_is_active(effective_mode):
        return "dual_agent"
    if reviewer_mode_is_single_agent(effective_mode):
        return "single_agent"
    return "unresolved"


def _governance_mode(payload: Mapping[str, object]) -> str:
    governance = _mapping(payload.get("governance"))
    bridge_config = _mapping(governance.get("bridge_config"))
    return _text(bridge_config.get("operator_interaction_mode"))


def _posture_has_runtime_truth(posture: Mapping[str, object]) -> bool:
    if not posture:
        return False
    return bool(
        posture.get("actors")
        or _text(posture.get("interaction_mode")) not in {"", "unresolved"}
        or _text(posture.get("reviewer_mode")) not in {"", "single_agent"}
    )


def _text(value: object) -> str:
    return str(value or "").strip()



def authority_actions(inputs: AuthorityActionInputs) -> tuple[str, str]:
    if checkpoint_action_required(inputs.payload):
        return (
            _checkpoint_root_cause(inputs.payload, inputs.attention),
            "cut_checkpoint",
        )
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


def checkpoint_action_required(payload: Mapping[str, object]) -> bool:
    """Return whether startup checkpoint authority preempts runtime recovery."""
    push = _mapping(_mapping(payload.get("governance")).get("push_enforcement"))
    if push:
        if bool(push.get("checkpoint_required", False)):
            return True
        if not bool(push.get("safe_to_continue_editing", True)):
            return True
    push_decision = _mapping(payload.get("push_decision"))
    if str(push_decision.get("action") or "").strip() == "await_checkpoint":
        return True
    advisory_action = str(payload.get("advisory_action") or "").strip()
    return advisory_action == "checkpoint_before_continue"


def _checkpoint_root_cause(
    payload: Mapping[str, object],
    attention: Mapping[str, object],
) -> str:
    push = _mapping(_mapping(payload.get("governance")).get("push_enforcement"))
    reason = str(
        push.get("checkpoint_reason")
        or _mapping(payload.get("push_decision")).get("reason")
        or payload.get("advisory_reason")
        or ""
    ).strip()
    if reason:
        return (
            "The current worktree has exceeded the checkpoint budget; "
            f"reason={reason}."
        )
    return str(attention.get("summary") or "").strip() or (
        "The current worktree requires a checkpoint before more implementation."
    )


def reviewer_provider_from_payload(payload: Mapping[str, object]) -> str:
    collaboration = _mapping(payload.get("collaboration"))
    provider = str(collaboration.get("review_agent") or "").strip().lower()
    if provider:
        return provider
    assignments = collaboration.get("role_assignments")
    if isinstance(assignments, list):
        for row in assignments:
            item = _mapping(row)
            if str(item.get("role_id") or "").strip() != "review_agent":
                continue
            provider = str(item.get("provider") or item.get("agent_id") or "").strip().lower()
            if provider:
                return provider
    return "codex"
