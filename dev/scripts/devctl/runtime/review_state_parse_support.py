"""Support helpers shared by review-state parsing."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .control_state import _int, _mapping, _string, _string_rows
from .review_state_models import (
    ConductorCapabilityState,
    RecoveryAssessmentState,
    RecoveryDecisionState,
    RecoveryDiagnosisState,
    RecoveryEvidenceState,
    ReviewAttentionState,
    ReviewBridgeState,
)
from .review_state_semantics import is_pending_implementer_state


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _optional_bool(mapping: Mapping[str, object], key: str) -> bool | None:
    """Preserve explicit unknown booleans instead of coercing them to False."""
    if key not in mapping:
        return None
    value = mapping.get(key)
    if value is None:
        return None
    return _bool(value)


def bridge_ack_state(
    *,
    bridge: Mapping[str, object],
    implementer_ack: str,
) -> str:
    """Classify implementer ACK state from bridge-backed projections."""
    if is_pending_implementer_state(
        implementer_status=_string(bridge.get("claude_status")),
        implementer_ack=implementer_ack,
    ):
        return "pending"
    if not implementer_ack:
        return "missing"
    if _bool(bridge.get("claude_ack_current")):
        return "current"
    return "stale"


def conductor_capability_state_from_payload(
    value: object,
) -> ConductorCapabilityState | None:
    """Parse one typed conductor-capability payload when present."""
    mapping = _mapping(value)
    if not mapping:
        return None
    return ConductorCapabilityState(
        provider=_string(mapping.get("provider")),
        role=_string(mapping.get("role")),
        startup_context_command=_string(mapping.get("startup_context_command")),
        may_edit_repo=_bool(mapping.get("may_edit_repo")),
        requires_explicit_takeover=_bool(
            mapping.get("requires_explicit_takeover")
        ),
        worker_unavailable_policy=_string(
            mapping.get("worker_unavailable_policy")
        ),
        queue_policy=_string(mapping.get("queue_policy")),
        takeover_command=_string(mapping.get("takeover_command")),
        status_summary=_string(mapping.get("status_summary")),
    )


def review_bridge_state_from_payload(
    *,
    bridge: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
) -> ReviewBridgeState:
    """Parse the typed bridge projection shared by review-state surfaces."""
    return ReviewBridgeState(
        overall_state=_string(bridge_liveness.get("overall_state")) or "unknown",
        codex_poll_state=_string(bridge_liveness.get("codex_poll_state")) or "unknown",
        reviewer_freshness=_string(bridge_liveness.get("reviewer_freshness"))
        or "unknown",
        reviewer_mode=_string(bridge.get("reviewer_mode")) or "single_agent",
        last_codex_poll_utc=_string(bridge.get("last_codex_poll_utc")),
        last_codex_poll_age_seconds=_int(
            bridge_liveness.get("last_codex_poll_age_seconds")
        ),
        last_worktree_hash=_string(bridge.get("last_worktree_hash")),
        current_instruction=_string(bridge.get("current_instruction")),
        open_findings=_string(bridge.get("open_findings")),
        claude_status=_string(bridge.get("claude_status")),
        claude_ack=_string(bridge.get("claude_ack")),
        claude_ack_current=_bool(bridge.get("claude_ack_current")),
        current_instruction_revision=_string(bridge.get("current_instruction_revision")),
        claude_ack_revision=_string(bridge.get("claude_ack_revision")),
        last_reviewed_scope=_string(bridge.get("last_reviewed_scope")),
        launch_truth=_string(bridge.get("launch_truth")),
        effective_reviewer_mode=_string(bridge.get("effective_reviewer_mode")),
        implementer_state_hash=_string(bridge.get("implementer_state_hash")),
        reviewed_hash_current=_optional_bool(bridge, "reviewed_hash_current"),
        review_needed=_optional_bool(bridge, "review_needed"),
        review_accepted=_bool(bridge.get("review_accepted")),
        implementer_completion_stall=bool(bridge.get("implementer_completion_stall")),
        publisher_running=bool(bridge.get("publisher_running")),
        codex_conductor_active=_bool(bridge.get("codex_conductor_active")),
        claude_conductor_active=_bool(bridge.get("claude_conductor_active")),
        reviewer_capability=conductor_capability_state_from_payload(
            bridge.get("reviewer_capability") or bridge_liveness.get("reviewer_capability")
        ),
        implementer_capability=conductor_capability_state_from_payload(
            bridge.get("implementer_capability")
            or bridge_liveness.get("implementer_capability")
        ),
    )


def attention_state_from_mapping(
    mapping: Mapping[str, object],
    *,
    recovery_assessment: RecoveryAssessmentState | None = None,
) -> ReviewAttentionState | None:
    if recovery_assessment is not None:
        return attention_state_from_recovery_assessment(recovery_assessment)
    if not mapping:
        return None
    return ReviewAttentionState(
        status=_string(mapping.get("status")) or "unknown",
        owner=_string(mapping.get("owner")) or "system",
        summary=_string(mapping.get("summary")),
        recommended_action=_string(mapping.get("recommended_action")),
        recommended_command=_string(mapping.get("recommended_command")),
    )


def attention_state_from_recovery_assessment(
    recovery_assessment: RecoveryAssessmentState,
) -> ReviewAttentionState:
    diagnosis = recovery_assessment.diagnosis
    decision = recovery_assessment.decision
    return ReviewAttentionState(
        status=diagnosis.status or "unknown",
        owner=decision.execution_owner or "system",
        summary=diagnosis.root_cause,
        recommended_action=decision.rationale,
        recommended_command=decision.command,
    )


def attention_projection_warning(
    *,
    raw_attention: Mapping[str, object],
    normalized_attention: ReviewAttentionState | None,
    recovery_assessment: RecoveryAssessmentState | None,
) -> str:
    if recovery_assessment is None or not raw_attention or normalized_attention is None:
        return ""
    mismatched_fields = [
        field_name
        for field_name, normalized_value in (
            ("status", normalized_attention.status),
            ("owner", normalized_attention.owner),
            ("summary", normalized_attention.summary),
            ("recommended_action", normalized_attention.recommended_action),
            ("recommended_command", normalized_attention.recommended_command),
        )
        if _string(raw_attention.get(field_name)) != normalized_value
    ]
    if not mismatched_fields:
        return ""
    return (
        "review_state.attention normalized from recovery_assessment projection: "
        + ", ".join(mismatched_fields)
    )


def recovery_assessment_from_mapping(
    mapping: Mapping[str, object],
) -> RecoveryAssessmentState | None:
    if not mapping:
        return None
    diagnosis = _mapping(mapping.get("diagnosis"))
    decision = _mapping(mapping.get("decision"))
    if not diagnosis and not decision:
        return None
    return RecoveryAssessmentState(
        diagnosis=RecoveryDiagnosisState(
            status=_string(diagnosis.get("status")) or "unknown",
            root_cause=_string(diagnosis.get("root_cause")),
            supporting_causes=_string_rows(diagnosis.get("supporting_causes")),
            evidence=_recovery_evidence_rows(diagnosis.get("evidence")),
            affected_surfaces=_string_rows(diagnosis.get("affected_surfaces")),
            expected_healthy_state=_string(diagnosis.get("expected_healthy_state")),
        ),
        decision=RecoveryDecisionState(
            action_id=_string(decision.get("action_id")),
            command=_string(decision.get("command")),
            execution_owner=_string(decision.get("execution_owner")),
            rationale=_string(decision.get("rationale")),
            blocked_alternatives=_string_rows(decision.get("blocked_alternatives")),
            can_auto_fix=_bool(decision.get("can_auto_fix")),
            requires_approval=_bool(decision.get("requires_approval")),
            next_expected_state=_string(decision.get("next_expected_state")),
        ),
    )


def _recovery_evidence_rows(value: object) -> tuple[RecoveryEvidenceState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    rows: list[RecoveryEvidenceState] = []
    for item in value:
        mapping = _mapping(item)
        if not mapping:
            continue
        rows.append(
            RecoveryEvidenceState(
                code=_string(mapping.get("code")),
                surface=_string(mapping.get("surface")),
                field=_string(mapping.get("field")),
                value=_string(mapping.get("value")),
                detail=_string(mapping.get("detail")),
            )
        )
    return tuple(rows)
