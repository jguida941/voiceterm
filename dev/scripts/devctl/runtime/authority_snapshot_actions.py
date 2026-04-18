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
