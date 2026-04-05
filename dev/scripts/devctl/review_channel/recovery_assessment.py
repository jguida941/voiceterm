"""Canonical typed recovery diagnosis/decision authority for review surfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..runtime.review_state_models import (
    RecoveryAssessmentState,
    RecoveryDecisionState,
    RecoveryDiagnosisState,
    RecoveryEvidenceState,
    ReviewAttentionState,
    ReviewCurrentSessionState,
)
from .attention_classify import classify_attention_status, extract_attention_context
from .peer_liveness import AttentionStatus
from .peer_recovery import (
    REVIEW_CHANNEL_RENDER_BRIDGE_COMMAND,
    STALE_PEER_RECOVERY,
)

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
    return RecoveryAssessmentState(
        diagnosis=RecoveryDiagnosisState(
            status=status,
            root_cause=_root_cause(status),
            supporting_causes=_supporting_causes(
                status=status,
                ctx=ctx,
                current_session=session,
                contract_errors=errors,
            ),
            evidence=_evidence_rows(
                status=status,
                ctx=ctx,
                current_session=session,
                contract_errors=errors,
            ),
            affected_surfaces=_AFFECTED_SURFACES,
            expected_healthy_state=_EXPECTED_HEALTHY_STATE,
        ),
        decision=_decision_state(
            status=status,
            ctx=ctx,
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


def _decision_state(
    *,
    status: str,
    ctx,
) -> RecoveryDecisionState:
    entry = _recovery_entry(status)
    action_id = _action_id(status=status, ctx=ctx)
    command = _command(status=status, ctx=ctx, default=str(entry.get("recommended_command") or ""))
    return RecoveryDecisionState(
        action_id=action_id,
        command=command,
        execution_owner=str(entry.get("owner") or ""),
        rationale=str(entry.get("recovery") or ""),
        blocked_alternatives=_blocked_alternatives(status=status),
        can_auto_fix=action_id in {
            "ensure_runtime",
            "render_bridge",
            "reset_implementer_state",
            "refresh_review_status",
        },
        requires_approval=action_id in {
            "cut_checkpoint",
            "relaunch_review_loop",
            "recover_implementer",
            "resume_live_review_loop",
        },
        next_expected_state="healthy",
    )


def _action_id(*, status: str, ctx) -> str:
    if status == AttentionStatus.HEALTHY.value:
        return "continue_scoped_loop"
    if status == AttentionStatus.INACTIVE.value:
        return "resume_live_review_loop"
    if status in {
        AttentionStatus.RUNTIME_MISSING.value,
        "publisher_missing",
        "publisher_failed_start",
        "publisher_detached_exit",
    }:
        return "ensure_runtime"
    if status in {
        AttentionStatus.REVIEWER_HEARTBEAT_MISSING.value,
        AttentionStatus.REVIEWER_HEARTBEAT_STALE.value,
        AttentionStatus.REVIEWER_OVERDUE.value,
        AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value,
    }:
        return "relaunch_review_loop"
    if status in {
        AttentionStatus.REVIEWER_POLL_DUE.value,
        AttentionStatus.WAITING_ON_PEER.value,
    }:
        return "refresh_review_status"
    if status == AttentionStatus.BRIDGE_CONTRACT_ERROR.value:
        return (
            "render_bridge"
            if _can_render_bridge(ctx.bridge_liveness)
            else "refresh_review_status"
        )
    if status == AttentionStatus.REVIEWER_SUPERVISOR_REQUIRED.value:
        return "start_reviewer_follow_loop"
    if status in {
        AttentionStatus.CLAUDE_STATUS_MISSING.value,
        AttentionStatus.IMPLEMENTER_COMPLETION_STALL.value,
    }:
        return "resume_implementer_work"
    if status in {
        AttentionStatus.CLAUDE_ACK_MISSING.value,
        AttentionStatus.CLAUDE_ACK_STALE.value,
    }:
        return "acknowledge_current_instruction"
    if status == AttentionStatus.IMPLEMENTER_STATE_RESET_REQUIRED.value:
        return "reset_implementer_state"
    if status == AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED.value:
        return "recover_implementer"
    if status == AttentionStatus.CHECKPOINT_REQUIRED.value:
        return "cut_checkpoint"
    if status in {
        AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED.value,
        AttentionStatus.REVIEWED_HASH_STALE.value,
    }:
        return "refresh_reviewer_verdict"
    if status == AttentionStatus.DUAL_AGENT_IDLE.value:
        return "start_reviewer_follow_loop"
    if status == AttentionStatus.REVIEWER_COMPLETION_UNRECORDED.value:
        return "cut_checkpoint"
    return "refresh_review_status"


def _command(*, status: str, ctx, default: str) -> str:
    if status == AttentionStatus.BRIDGE_CONTRACT_ERROR.value and _can_render_bridge(
        ctx.bridge_liveness
    ):
        return REVIEW_CHANNEL_RENDER_BRIDGE_COMMAND
    return default.strip()


def _blocked_alternatives(*, status: str) -> tuple[str, ...]:
    if status == AttentionStatus.HEALTHY.value:
        return ()
    if status == AttentionStatus.CHECKPOINT_REQUIRED.value:
        return ("continue_editing_without_checkpoint",)
    if status in {
        AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value,
        AttentionStatus.REVIEWER_HEARTBEAT_MISSING.value,
        AttentionStatus.REVIEWER_HEARTBEAT_STALE.value,
        AttentionStatus.REVIEWER_OVERDUE.value,
    }:
        return ("treat_detached_or_stale_runtime_as_live",)
    if status == AttentionStatus.IMPLEMENTER_STATE_RESET_REQUIRED.value:
        return ("launch_or_recover_claude_without_clearing_stale_state",)
    if status == AttentionStatus.BRIDGE_CONTRACT_ERROR.value:
        return ("trust_inconsistent_bridge_sections",)
    if status in {
        AttentionStatus.CLAUDE_ACK_MISSING.value,
        AttentionStatus.CLAUDE_ACK_STALE.value,
    }:
        return ("continue_coding_without_current_ack",)
    if status in {
        AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED.value,
        AttentionStatus.REVIEWED_HASH_STALE.value,
    }:
        return ("promote_next_slice_without_refreshing_review",)
    if status == AttentionStatus.REVIEWER_COMPLETION_UNRECORDED.value:
        return ("treat_heartbeat_acceptance_as_valid_checkpoint",)
    return ("ignore_recovery_signal",)


def _supporting_causes(
    *,
    status: str,
    ctx,
    current_session: ReviewCurrentSessionState,
    contract_errors: Sequence[str],
) -> tuple[str, ...]:
    causes: list[str] = []
    if ctx.launch_truth:
        causes.append(f"launch_truth:{ctx.launch_truth}")
    if ctx.reviewer_freshness:
        causes.append(f"reviewer_freshness:{ctx.reviewer_freshness}")
    if ctx.review_needed:
        causes.append("review_needed")
    if not ctx.claude_ack_current and current_session.current_instruction_revision:
        causes.append("implementer_ack_not_current")
    if ctx.implementer_completion_stall:
        causes.append("implementer_completion_stall")
    if ctx.session_hint_state:
        causes.append(f"implementer_session_hint:{ctx.session_hint_state}")
    if not bool(ctx.bridge_liveness.get("codex_conductor_active")) and status in {
        AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value,
        AttentionStatus.REVIEWER_HEARTBEAT_MISSING.value,
        AttentionStatus.REVIEWER_HEARTBEAT_STALE.value,
        AttentionStatus.REVIEWER_OVERDUE.value,
    }:
        causes.append("reviewer_conductor_inactive")
    if not bool(ctx.bridge_liveness.get("claude_conductor_active")) and status in {
        AttentionStatus.IMPLEMENTER_STATE_RESET_REQUIRED.value,
        AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED.value,
        AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value,
    }:
        causes.append("implementer_conductor_inactive")
    if ctx.checkpoint_required or not ctx.safe_to_continue_editing:
        causes.append("checkpoint_budget_exhausted")
    if status == AttentionStatus.REVIEWER_COMPLETION_UNRECORDED.value:
        if ctx.last_checkpoint_action:
            causes.append(f"last_checkpoint_action:{ctx.last_checkpoint_action}")
        elif ctx.poll_status_action:
            causes.append(f"poll_status_action:{ctx.poll_status_action}")
    causes.extend(f"contract_error:{error}" for error in contract_errors[:3])
    return tuple(dict.fromkeys(cause for cause in causes if cause))


def _evidence_rows(
    *,
    status: str,
    ctx,
    current_session: ReviewCurrentSessionState,
    contract_errors: Sequence[str],
) -> tuple[RecoveryEvidenceState, ...]:
    rows = [
        RecoveryEvidenceState(
            code="diagnosis_status",
            surface="attention_classifier",
            field="status",
            value=status,
            detail="Priority-ordered recovery diagnosis from typed bridge liveness.",
        ),
        RecoveryEvidenceState(
            code="reviewer_mode",
            surface="bridge_liveness",
            field="reviewer_mode",
            value=str(ctx.bridge_liveness.get("reviewer_mode") or ""),
            detail="Declared reviewer mode used by the classifier.",
        ),
        RecoveryEvidenceState(
            code="overall_state",
            surface="bridge_liveness",
            field="overall_state",
            value=str(ctx.overall_state or ""),
            detail="Overall bridge liveness classification.",
        ),
        RecoveryEvidenceState(
            code="reviewer_freshness",
            surface="bridge_liveness",
            field="reviewer_freshness",
            value=str(ctx.reviewer_freshness or ""),
            detail="Freshness signal seen by the reviewer loop.",
        ),
        RecoveryEvidenceState(
            code="current_instruction_revision",
            surface="current_session",
            field="current_instruction_revision",
            value=str(current_session.current_instruction_revision or ""),
            detail="Current reviewer instruction revision.",
        ),
        RecoveryEvidenceState(
            code="implementer_ack_state",
            surface="current_session",
            field="implementer_ack_state",
            value=str(current_session.implementer_ack_state or ""),
            detail="Implementer ACK freshness for the live instruction.",
        ),
    ]
    if status in {
        AttentionStatus.IMPLEMENTER_STATE_RESET_REQUIRED.value,
        AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED.value,
        AttentionStatus.CLAUDE_ACK_MISSING.value,
        AttentionStatus.CLAUDE_ACK_STALE.value,
    }:
        rows.append(
            RecoveryEvidenceState(
                code="claude_ack_current",
                surface="bridge_liveness",
                field="claude_ack_current",
                value=_bool_string(ctx.claude_ack_current),
                detail="Whether Claude Ack matches the current instruction revision.",
            )
        )
    if status in {
        AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value,
        AttentionStatus.BRIDGE_CONTRACT_ERROR.value,
        AttentionStatus.RUNTIME_MISSING.value,
    }:
        rows.append(
            RecoveryEvidenceState(
                code="launch_truth",
                surface="bridge_liveness",
                field="launch_truth",
                value=str(ctx.launch_truth or ""),
                detail="Launch-truth classification for the dual-agent runtime.",
            )
        )
    if status in {
        AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED.value,
        AttentionStatus.REVIEWED_HASH_STALE.value,
    }:
        rows.append(
            RecoveryEvidenceState(
                code="review_needed",
                surface="bridge_liveness",
                field="review_needed",
                value=_bool_string(ctx.review_needed),
                detail="Whether reviewed hash parity says reviewer follow-up is required.",
            )
        )
    if status == AttentionStatus.CHECKPOINT_REQUIRED.value:
        rows.append(
            RecoveryEvidenceState(
                code="checkpoint_required",
                surface="push_enforcement",
                field="checkpoint_required",
                value=_bool_string(ctx.checkpoint_required),
                detail="Repo governance checkpoint budget state.",
            )
        )
    if status == AttentionStatus.REVIEWER_COMPLETION_UNRECORDED.value:
        rows.append(
            RecoveryEvidenceState(
                code="last_checkpoint_action",
                surface="bridge_metadata",
                field="last_checkpoint_action",
                value=str(ctx.last_checkpoint_action or ""),
                detail=(
                    "Durable checkpoint provenance from bridge metadata; expected "
                    "'reviewer-checkpoint' when verdict shows acceptance."
                ),
            )
        )
    for error in contract_errors[:3]:
        rows.append(
            RecoveryEvidenceState(
                code="contract_error",
                surface="bridge_contract",
                field="error",
                value=error,
            )
        )
    return tuple(rows)


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


def _can_render_bridge(bridge_liveness: Mapping[str, object]) -> bool:
    return bool(bridge_liveness.get("codex_conductor_active")) or bool(
        bridge_liveness.get("claude_conductor_active")
    )


def _mapping(value: Mapping[str, object] | None) -> dict[str, object] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _string_items(values: Sequence[object] | None) -> list[str]:
    return [str(value).strip() for value in values or () if str(value).strip()]


def _bool_string(value: object) -> str:
    return "true" if bool(value) else "false"
