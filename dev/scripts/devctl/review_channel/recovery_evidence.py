"""Recovery evidence and supporting-cause builders for diagnosis state."""

from __future__ import annotations

from collections.abc import Sequence

from ..runtime.review_state_models import (
    RecoveryEvidenceState,
    ReviewCurrentSessionState,
)
from .peer_liveness import AttentionStatus


def build_supporting_causes(
    *,
    status: str,
    ctx,
    current_session: ReviewCurrentSessionState,
    contract_errors: Sequence[str],
) -> tuple[str, ...]:
    """Collect supporting-cause strings for the recovery diagnosis."""
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
    if status == AttentionStatus.VERIFICATION_CAPABILITY_MISSING.value:
        if ctx.bridge_liveness.get("mutation_owner"):
            causes.append(f"mutation_owner:{ctx.bridge_liveness.get('mutation_owner')}")
        if ctx.bridge_liveness.get("verification_owner"):
            causes.append(
                f"verification_owner:{ctx.bridge_liveness.get('verification_owner')}"
            )
        causes.append("mutation_capability_live")
        causes.append("verification_capability_missing")

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


def build_evidence_rows(
    *,
    status: str,
    ctx,
    current_session: ReviewCurrentSessionState,
    contract_errors: Sequence[str],
) -> tuple[RecoveryEvidenceState, ...]:
    """Build the typed evidence row sequence for the recovery diagnosis."""
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
        AttentionStatus.VERIFICATION_CAPABILITY_MISSING.value,
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
    if status == AttentionStatus.VERIFICATION_CAPABILITY_MISSING.value:
        rows.extend(
            (
                RecoveryEvidenceState(
                    code="mutation_owner",
                    surface="bridge_liveness",
                    field="mutation_owner",
                    value=str(ctx.bridge_liveness.get("mutation_owner") or ""),
                    detail="Actor currently holding repo mutation authority.",
                ),
                RecoveryEvidenceState(
                    code="verification_owner",
                    surface="bridge_liveness",
                    field="verification_owner",
                    value=str(ctx.bridge_liveness.get("verification_owner") or ""),
                    detail="Configured actor expected to hold verification authority.",
                ),
                RecoveryEvidenceState(
                    code="verification_status",
                    surface="bridge_liveness",
                    field="verification_status",
                    value=str(ctx.bridge_liveness.get("verification_status") or ""),
                    detail="Liveness state for the configured verification owner.",
                ),
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


def _bool_string(value: object) -> str:
    return "true" if bool(value) else "false"
