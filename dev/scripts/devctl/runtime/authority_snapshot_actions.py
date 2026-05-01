"""Action and reviewer-mode helpers extracted from authority snapshot assembly."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .authority_snapshot_core import _mapping


@dataclass(frozen=True, slots=True)
class AuthorityActionInputs:
    payload: Mapping[str, object]
    reviewer_gate: Mapping[str, object]
    attention: Mapping[str, object]
    doctor: Mapping[str, object]
    diagnosis: Mapping[str, object]
    decision: Mapping[str, object]
    recovery_authority: Mapping[str, object]


def authority_modes(
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
