"""Field coercion helpers for typed collaboration-state payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .control_state import _int, _mapping, _string
from .review_state_models import (
    CollaborationArbitrationState,
    CollaborationParticipantState,
    CollaborationPeerReviewState,
    CollaborationReadyGateState,
    CollaborationRestartState,
    CollaborationRoleAssignmentState,
    DelegatedWorkReceiptState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
)
from .review_state_parse_support import _bool


def _peer_review_state_from_mapping(
    mapping: Mapping[str, object],
    *,
    current_session: ReviewCurrentSessionState,
) -> CollaborationPeerReviewState:
    if not mapping:
        return CollaborationPeerReviewState(
            current_instruction=current_session.current_instruction,
            current_instruction_revision=current_session.current_instruction_revision,
            open_findings=current_session.open_findings,
            implementer_status=current_session.implementer_status,
            implementer_ack=current_session.implementer_ack,
            implementer_ack_state=current_session.implementer_ack_state,
            implementer_state_hash=current_session.implementer_state_hash,
            last_reviewed_scope=current_session.last_reviewed_scope,
        )
    return CollaborationPeerReviewState(
        current_instruction=_string(mapping.get("current_instruction")),
        current_instruction_revision=_string(
            mapping.get("current_instruction_revision")
        ),
        open_findings=_string(mapping.get("open_findings")),
        implementer_status=_string(mapping.get("implementer_status")),
        implementer_ack=_string(mapping.get("implementer_ack")),
        implementer_ack_state=_string(mapping.get("implementer_ack_state")) or "unknown",
        implementer_state_hash=_string(mapping.get("implementer_state_hash")),
        last_reviewed_scope=_string(mapping.get("last_reviewed_scope")),
    )


def _arbitration_state_from_mapping(
    mapping: Mapping[str, object],
) -> CollaborationArbitrationState:
    return CollaborationArbitrationState(
        status=_string(mapping.get("status")) or "clear",
        summary=_string(mapping.get("summary")),
        owner=_string(mapping.get("owner")),
    )


def _restart_state_from_mapping(
    mapping: Mapping[str, object],
    *,
    bridge: ReviewBridgeState,
) -> CollaborationRestartState:
    if not mapping:
        return CollaborationRestartState(
            status="fresh_start",
            resumable=False,
            source="",
            launch_truth=bridge.launch_truth,
            reviewer_mode=bridge.reviewer_mode,
            effective_reviewer_mode=bridge.effective_reviewer_mode,
            last_codex_poll_utc=bridge.last_codex_poll_utc,
            last_worktree_hash=bridge.last_worktree_hash,
        )
    return CollaborationRestartState(
        status=_string(mapping.get("status")) or "fresh_start",
        resumable=_bool(mapping.get("resumable")),
        source=_string(mapping.get("source")),
        launch_truth=_string(mapping.get("launch_truth")) or bridge.launch_truth,
        reviewer_mode=_string(mapping.get("reviewer_mode")) or bridge.reviewer_mode,
        effective_reviewer_mode=_string(mapping.get("effective_reviewer_mode"))
        or bridge.effective_reviewer_mode,
        last_codex_poll_utc=_string(mapping.get("last_codex_poll_utc"))
        or bridge.last_codex_poll_utc,
        last_worktree_hash=_string(mapping.get("last_worktree_hash"))
        or bridge.last_worktree_hash,
    )


def _ready_gates_from_value(
    value: object,
) -> tuple[CollaborationReadyGateState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        CollaborationReadyGateState(
            gate_id=_string(mapping.get("gate_id")),
            status=_string(mapping.get("status")) or "unknown",
            summary=_string(mapping.get("summary")),
        )
        for row in value
        if (mapping := _mapping(row)) and _string(mapping.get("gate_id"))
    )


def _role_assignments_from_value(
    value: object,
) -> tuple[CollaborationRoleAssignmentState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        CollaborationRoleAssignmentState(
            role_id=_string(mapping.get("role_id")),
            agent_id=_string(mapping.get("agent_id")),
            provider=_string(mapping.get("provider")),
            display_name=_string(mapping.get("display_name")),
            status=_string(mapping.get("status")) or "unknown",
            source=_string(mapping.get("source")),
            session_name=_string(mapping.get("session_name")),
            live=_bool(mapping.get("live")),
        )
        for row in value
        if (mapping := _mapping(row)) and _string(mapping.get("role_id"))
    )


def _participants_from_value(
    value: object,
) -> tuple[CollaborationParticipantState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        CollaborationParticipantState(
            agent_id=_string(mapping.get("agent_id")),
            provider=_string(mapping.get("provider")),
            display_name=_string(mapping.get("display_name"))
            or _string(mapping.get("agent_id")),
            role=_string(mapping.get("role")),
            session_name=_string(mapping.get("session_name")),
            live=_bool(mapping.get("live")),
            status=_string(mapping.get("status")) or "unknown",
            capture_mode=_string(mapping.get("capture_mode")),
            approval_mode=_string(mapping.get("approval_mode")),
            supervision_mode=_string(mapping.get("supervision_mode")),
            prepared_at=_string(mapping.get("prepared_at")),
            metadata_path=_string(mapping.get("metadata_path")),
            log_path=_string(mapping.get("log_path")),
            launch_command=_string(mapping.get("launch_command")),
            requested_worker_budget=_optional_int(
                mapping.get("requested_worker_budget")
            ),
            planned_lane_count=_int(mapping.get("planned_lane_count")),
        )
        for row in value
        if (mapping := _mapping(row)) and _string(mapping.get("agent_id"))
    )


def _delegated_work_from_value(
    value: object,
) -> tuple[DelegatedWorkReceiptState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        DelegatedWorkReceiptState(
            receipt_id=_string(mapping.get("receipt_id")),
            agent_id=_string(mapping.get("agent_id")),
            provider=_string(mapping.get("provider")),
            role=_string(mapping.get("role")),
            owner_session=_string(mapping.get("owner_session")),
            source=_string(mapping.get("source")),
            status=_string(mapping.get("status")) or "unknown",
            lane=_string(mapping.get("lane")),
            mp_scope=_string(mapping.get("mp_scope")),
            worktree=_string(mapping.get("worktree")),
            branch=_string(mapping.get("branch")),
            live=_bool(mapping.get("live")),
        )
        for row in value
        if (mapping := _mapping(row)) and _string(mapping.get("receipt_id"))
    )


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return _int(value)
