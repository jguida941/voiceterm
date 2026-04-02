"""Builders for the typed collaboration-session review-state contract."""

from __future__ import annotations

from pathlib import Path

from ..runtime.review_state_models import (
    CollaborationPeerReviewState,
    CollaborationSessionState,
    ReviewCurrentSessionState,
)
from .collaboration_session_roster import (
    _build_delegated_work,
    _build_participants,
    _build_role_assignments,
    _text,
)
from .collaboration_session_status import (
    _agent_for_role,
    _build_arbitration,
    _build_ready_gates,
    _build_restart_state,
    _collaboration_status,
    _operator_mode,
)
from .session_probe import ConductorSessionRecord, load_conductor_sessions


def build_collaboration_session(
    *,
    timestamp: str,
    plan_id: str,
    session_id: str,
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    attention: Mapping[str, object] | None = None,
    session_output_root: Path | None = None,
) -> CollaborationSessionState:
    """Build the typed collaboration/session state for review-channel runtime."""
    session_records = (
        load_conductor_sessions(session_output_root=session_output_root)
        if session_output_root is not None
        else ()
    )
    participants = _build_participants(session_records)
    role_assignments = _build_role_assignments(session_records)
    delegated_work = _build_delegated_work(session_records)
    peer_review = CollaborationPeerReviewState(
        current_instruction=current_session.current_instruction,
        current_instruction_revision=current_session.current_instruction_revision,
        open_findings=current_session.open_findings,
        implementer_status=current_session.implementer_status,
        implementer_ack=current_session.implementer_ack,
        implementer_ack_state=current_session.implementer_ack_state,
        implementer_state_hash=current_session.implementer_state_hash,
        last_reviewed_scope=current_session.last_reviewed_scope,
    )
    reviewer_mode = _text(bridge_liveness.get("reviewer_mode")) or "tools_only"
    effective_mode = _text(bridge_liveness.get("effective_reviewer_mode")) or reviewer_mode
    current_slice = current_session.current_instruction or current_session.last_reviewed_scope
    return CollaborationSessionState(
        schema_version=1,
        contract_id="CollaborationSession",
        session_id=session_id or "review-channel",
        plan_id=plan_id,
        status=_collaboration_status(
            participants=participants,
            delegated_work=delegated_work,
            current_session=current_session,
        ),
        reviewer_mode=effective_mode,
        operator_mode=_operator_mode(attention),
        lead_agent=_agent_for_role(role_assignments, "lead_agent"),
        review_agent=_agent_for_role(role_assignments, "review_agent"),
        coding_agent=_agent_for_role(role_assignments, "coding_agent"),
        current_slice=current_slice,
        peer_review=peer_review,
        arbitration=_build_arbitration(attention),
        restart=_build_restart_state(
            participants=participants,
            delegated_work=delegated_work,
            bridge_liveness=bridge_liveness,
            reviewer_mode=reviewer_mode,
            effective_mode=effective_mode,
            current_session=current_session,
        ),
        ready_gates=_build_ready_gates(
            participants=participants,
            delegated_work=delegated_work,
            session_records=session_records,
            bridge_liveness=bridge_liveness,
            reviewer_mode=effective_mode,
            current_session=current_session,
        ),
        role_assignments=role_assignments,
        participants=participants,
        delegated_work=delegated_work,
    )
