"""Status, arbitration, and readiness builders for collaboration-session state."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_state_semantics import is_missing_instruction
from ..runtime.review_state_models import (
    CollaborationArbitrationState,
    CollaborationParticipantState,
    CollaborationReadyGateState,
    CollaborationRestartState,
    CollaborationRoleAssignmentState,
    DelegatedWorkReceiptState,
    ReviewCurrentSessionState,
)
from ..runtime.role_profile import TandemRole
from .collaboration_session_roster import _text
from .session_probe import ConductorSessionRecord


def _build_arbitration(
    attention: Mapping[str, object] | None,
) -> CollaborationArbitrationState:
    if not isinstance(attention, Mapping):
        return CollaborationArbitrationState(status="clear", summary="", owner="")
    owner = _text(attention.get("owner"))
    summary = _text(attention.get("summary"))
    if owner == "operator" and summary:
        return CollaborationArbitrationState(
            status="operator_attention",
            summary=summary,
            owner=owner,
        )
    if owner and owner != "system" and summary:
        return CollaborationArbitrationState(
            status="attention",
            summary=summary,
            owner=owner,
        )
    return CollaborationArbitrationState(status="clear", summary="", owner=owner)


def _build_restart_state(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
    bridge_liveness: Mapping[str, object],
    reviewer_mode: str,
    effective_mode: str,
    current_session: ReviewCurrentSessionState,
) -> CollaborationRestartState:
    if any(participant.live for participant in participants):
        status = "live"
        source = (
            "remote_control_attachment"
            if any(
                participant.live and participant.capture_mode == "remote-control"
                for participant in participants
            )
            else "session_metadata"
        )
    elif participants or delegated_work:
        status = "resumable"
        source = "session_metadata"
    elif (
        not is_missing_instruction(current_session.current_instruction)
        or current_session.open_findings
    ):
        status = "handoff_only"
        source = "review_state"
    else:
        status = "fresh_start"
        source = ""
    return CollaborationRestartState(
        status=status,
        resumable=status != "fresh_start",
        source=source,
        launch_truth=_text(bridge_liveness.get("launch_truth")),
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_mode,
        last_codex_poll_utc=_text(bridge_liveness.get("last_codex_poll_utc")),
        last_worktree_hash=_text(bridge_liveness.get("last_worktree_hash")),
    )


def _build_ready_gates(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
    session_records: tuple[ConductorSessionRecord, ...],
    bridge_liveness: Mapping[str, object],
    reviewer_mode: str,
    current_session: ReviewCurrentSessionState,
) -> tuple[CollaborationReadyGateState, ...]:
    return (
        CollaborationReadyGateState(
            gate_id="runtime_truth",
            status=_runtime_gate_status(reviewer_mode, participants),
            summary=_runtime_gate_summary(reviewer_mode, participants),
        ),
        CollaborationReadyGateState(
            gate_id="review_truth",
            status=_review_gate_status(
                bridge_liveness,
                reviewer_mode=reviewer_mode,
            ),
            summary=_review_gate_summary(
                bridge_liveness,
                reviewer_mode=reviewer_mode,
            ),
        ),
        CollaborationReadyGateState(
            gate_id="implementer_state",
            status=_implementer_gate_status(
                current_session,
                reviewer_mode=reviewer_mode,
            ),
            summary=_implementer_gate_summary(
                current_session,
                reviewer_mode=reviewer_mode,
            ),
        ),
        CollaborationReadyGateState(
            gate_id="delegated_work",
            status=_delegated_gate_status(session_records, delegated_work),
            summary=_delegated_gate_summary(session_records, delegated_work),
        ),
    )


def _runtime_gate_status(
    reviewer_mode: str,
    participants: tuple[CollaborationParticipantState, ...],
) -> str:
    if reviewer_mode != "active_dual_agent":
        return "not_required"
    reviewer_live = any(
        participant.live and participant.role == TandemRole.REVIEWER.value
        for participant in participants
    )
    implementer_live = any(
        participant.live and participant.role == TandemRole.IMPLEMENTER.value
        for participant in participants
    )
    return "ready" if reviewer_live and implementer_live else "blocked"


def _runtime_gate_summary(
    reviewer_mode: str,
    participants: tuple[CollaborationParticipantState, ...],
) -> str:
    if reviewer_mode != "active_dual_agent":
        return (
            f"Compatibility reviewer mode `{reviewer_mode}` does not require "
            "paired reviewer/implementer conductors."
        )
    reviewer_live = any(
        participant.live and participant.role == TandemRole.REVIEWER.value
        for participant in participants
    )
    implementer_live = any(
        participant.live and participant.role == TandemRole.IMPLEMENTER.value
        for participant in participants
    )
    if reviewer_live and implementer_live:
        return "Live reviewer and implementer conductor sessions are present."
    return (
        "Compatibility active reviewer mode still requires live reviewer and "
        "implementer conductor sessions."
    )


def _review_gate_status(
    bridge_liveness: Mapping[str, object],
    *,
    reviewer_mode: str,
) -> str:
    if reviewer_mode != "active_dual_agent":
        return "not_required"
    if (
        bridge_liveness.get("review_needed")
        or bridge_liveness.get("reviewed_hash_current") is False
    ):
        return "blocked"
    return "ready"


def _review_gate_summary(
    bridge_liveness: Mapping[str, object],
    *,
    reviewer_mode: str,
) -> str:
    if reviewer_mode != "active_dual_agent":
        return "Single-agent reviewer mode does not require dual-agent review truth."
    if bridge_liveness.get("review_needed"):
        return "Reviewer follow-up is still required for the current worktree."
    if bridge_liveness.get("reviewed_hash_current") is False:
        return "The reviewed worktree hash is stale against the current tree."
    return "Reviewer truth is current for the visible worktree."


def _implementer_gate_status(
    current_session: ReviewCurrentSessionState,
    *,
    reviewer_mode: str,
) -> str:
    if reviewer_mode != "active_dual_agent":
        return "not_required"
    if is_missing_instruction(current_session.current_instruction):
        return "not_required"
    if current_session.implementer_ack_state == "current":
        return "ready"
    if current_session.implementer_ack_state in {"stale", "missing"}:
        return "blocked"
    return "pending"


def _implementer_gate_summary(
    current_session: ReviewCurrentSessionState,
    *,
    reviewer_mode: str,
) -> str:
    if reviewer_mode != "active_dual_agent":
        return (
            "Single-agent reviewer mode does not require a separate implementer ACK."
        )
    if is_missing_instruction(current_session.current_instruction):
        return "No active implementer instruction is present."
    if current_session.implementer_ack_state == "current":
        return "Implementer state matches the current instruction revision."
    return "Implementer state has not acknowledged the current instruction revision yet."


def _delegated_gate_status(
    session_records: tuple[ConductorSessionRecord, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
) -> str:
    requested_budget = sum(
        max(record.requested_worker_budget or 0, 0)
        for record in session_records
    )
    if requested_budget <= 0:
        return "not_requested"
    if delegated_work:
        return "planned"
    return "pending"


def _delegated_gate_summary(
    session_records: tuple[ConductorSessionRecord, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
) -> str:
    requested_budget = sum(
        max(record.requested_worker_budget or 0, 0)
        for record in session_records
    )
    if requested_budget <= 0:
        return "No worker fanout was requested for the current conductor sessions."
    if delegated_work:
        return (
            f"{len(delegated_work)} delegated lane receipt(s) were recorded by "
            "conductor session metadata."
        )
    return "Worker fanout was requested but no delegated lane receipts are available yet."


def _collaboration_status(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
    current_session: ReviewCurrentSessionState,
) -> str:
    if any(participant.live for participant in participants):
        return "live"
    if participants or delegated_work:
        return "resumable"
    if (
        not is_missing_instruction(current_session.current_instruction)
        or current_session.open_findings
    ):
        return "handoff_only"
    return "inactive"


def _operator_mode(attention: Mapping[str, object] | None) -> str:
    if not isinstance(attention, Mapping):
        return "manual"
    if _text(attention.get("owner")) == "operator":
        return "attention_required"
    return "manual"


def _agent_for_role(
    assignments: tuple[CollaborationRoleAssignmentState, ...],
    role_id: str,
) -> str:
    return next(
        (assignment.agent_id for assignment in assignments if assignment.role_id == role_id),
        "",
    )
