"""Canonical typed recovery diagnosis/decision authority for review surfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..runtime.review_state_models import (
    RecoveryAssessmentState,
    RecoveryDiagnosisState,
    ReviewAttentionState,
    ReviewCurrentSessionState,
)
from .attention_classify import classify_attention_status, extract_attention_context
from .peer_liveness import AttentionStatus
from .peer_recovery import STALE_PEER_RECOVERY
from .recovery_decision import build_decision_state
from .recovery_evidence import build_evidence_rows, build_supporting_causes

_AFFECTED_SURFACES = (
    "review-channel status",
    "review-channel doctor",
    "startup-context",
    "review-channel bridge-poll",
)
_EXPECTED_HEALTHY_STATE = (
    "The active review loop is live, reviewer freshness is fresh, bridge state is "
    "coherent, the implementer ACK matches the current instruction revision, and "
    "no recovery action is required."
)


def build_recovery_assessment(
    *,
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState | None = None,
    push_state: Mapping[str, object] | None = None,
    contract_errors: Sequence[object] | None = None,
    operator_interaction_mode: str = "",
) -> RecoveryAssessmentState:
    """Build the authoritative diagnosis/decision pair from typed review inputs."""
    liveness = dict(bridge_liveness)
    errors = _string_items(contract_errors)
    session = current_session or _fallback_current_session(liveness)
    ctx = extract_attention_context(
        liveness,
        push_state=_mapping(push_state),
        contract_errors=errors,
    )
    status = classify_attention_status(ctx)
    entry = _recovery_entry(status)
    return RecoveryAssessmentState(
        diagnosis=RecoveryDiagnosisState(
            status=status,
            root_cause=_root_cause(status),
            supporting_causes=build_supporting_causes(
                status=status,
                ctx=ctx,
                current_session=session,
                contract_errors=errors,
            ),
            evidence=build_evidence_rows(
                status=status,
                ctx=ctx,
                current_session=session,
                contract_errors=errors,
            ),
            affected_surfaces=_AFFECTED_SURFACES,
            expected_healthy_state=_EXPECTED_HEALTHY_STATE,
        ),
        decision=build_decision_state(
            status=status,
            ctx=ctx,
            operator_interaction_mode=operator_interaction_mode,
            recovery_entry=entry,
        ),
    )


def recovery_assessment_to_attention_payload(
    assessment: RecoveryAssessmentState | None,
) -> dict[str, object]:
    """Render the legacy attention payload as a pure projection of assessment."""
    if assessment is None:
        return {}
    status = str(assessment.diagnosis.status or "").strip()
    entry = _recovery_entry(status)
    return {
        "status": status,
        "owner": assessment.decision.execution_owner or str(entry.get("owner") or ""),
        "summary": assessment.diagnosis.root_cause or str(entry.get("summary") or ""),
        "recommended_action": (
            assessment.decision.rationale or str(entry.get("recovery") or "")
        ),
        "recommended_command": assessment.decision.command,
    }


def recovery_assessment_to_attention_state(
    assessment: RecoveryAssessmentState | None,
) -> ReviewAttentionState | None:
    """Project a typed attention state from the recovery assessment."""
    payload = recovery_assessment_to_attention_payload(assessment)
    if not payload:
        return None
    return ReviewAttentionState(
        status=str(payload.get("status") or ""),
        owner=str(payload.get("owner") or ""),
        summary=str(payload.get("summary") or ""),
        recommended_action=str(payload.get("recommended_action") or ""),
        recommended_command=str(payload.get("recommended_command") or ""),
    )


def _root_cause(status: str) -> str:
    return str(_recovery_entry(status).get("summary") or "").strip()


def _fallback_current_session(
    bridge_liveness: Mapping[str, object],
) -> ReviewCurrentSessionState:
    implementer_ack = str(bridge_liveness.get("claude_ack") or "")
    implementer_ack_state = (
        "current"
        if bool(bridge_liveness.get("claude_ack_current"))
        else "missing"
        if not implementer_ack.strip()
        else "stale"
    )
    return ReviewCurrentSessionState(
        current_instruction=str(bridge_liveness.get("current_instruction") or ""),
        current_instruction_revision=str(
            bridge_liveness.get("current_instruction_revision") or ""
        ),
        implementer_status=str(bridge_liveness.get("claude_status") or ""),
        implementer_ack=implementer_ack,
        implementer_ack_revision=str(bridge_liveness.get("claude_ack_revision") or ""),
        implementer_ack_state=implementer_ack_state,
        implementer_state_hash=str(bridge_liveness.get("implementer_state_hash") or ""),
        open_findings=str(bridge_liveness.get("open_findings") or ""),
        last_reviewed_scope=str(bridge_liveness.get("last_reviewed_scope") or ""),
    )


def _recovery_entry(status: str) -> Mapping[str, object]:
    entry = STALE_PEER_RECOVERY.get(status)
    if isinstance(entry, Mapping):
        return entry
    return STALE_PEER_RECOVERY[AttentionStatus.HEALTHY.value]


def _mapping(value: Mapping[str, object] | None) -> dict[str, object] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _string_items(values: Sequence[object] | None) -> list[str]:
    return [str(value).strip() for value in values or () if str(value).strip()]
