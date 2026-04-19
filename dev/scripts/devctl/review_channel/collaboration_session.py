"""Builders for the typed collaboration-session review-state contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from ..runtime.review_state_models import (
    CollaborationParticipantState,
    CollaborationPeerReviewState,
    CollaborationRoleAssignmentState,
    CollaborationSessionState,
    ReviewCurrentSessionState,
)
from ..runtime.role_profile import TandemRole, default_provider_for_role
from .collaboration_session_roster import (
    _build_delegated_work,
    _build_participants,
    _build_role_assignments,
)
from . import collaboration_session_local_reviewer as _local_reviewer
from .remote_control_attachment_artifact import load_remote_control_attachments
from .collaboration_session_coordination import (
    build_collaboration_ownership,
    collaboration_topology_mode,
    work_ownership_mode,
)
from .collaboration_session_status import (
    _agent_for_role,
    _build_arbitration,
    _build_ready_gates,
    _build_restart_state,
    _collaboration_status,
    _operator_mode,
)
from .collaboration_session_lane_owners import (
    owner_status as _owner_status,
    verification_owner as _verification_owner,
    watcher_owner as _watcher_owner,
)
from .session_probe import load_conductor_sessions

_text = _local_reviewer.text
_utcnow = _local_reviewer._utcnow
discover_latest_session = _local_reviewer.discover_latest_session
_local_reviewer_activity_is_fresh = _local_reviewer.local_reviewer_activity_is_fresh
_provider_packet_activity_is_fresh = _local_reviewer.provider_packet_activity_is_fresh


def build_collaboration_session(
    *,
    timestamp: str,
    plan_id: str,
    session_id: str,
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    attention: Mapping[str, object] | None = None,
    repo_root: Path | None = None,
    session_output_root: Path | None = None,
) -> CollaborationSessionState:
    """Build the typed collaboration/session state for review-channel runtime."""
    session_records = (
        load_conductor_sessions(session_output_root=session_output_root)
        if session_output_root is not None
        else ()
    )
    remote_attachments = (
        load_remote_control_attachments(
            output_root=session_output_root,
            active_only=True,
        )
        if session_output_root is not None
        else ()
    )
    reviewer_mode = _text(bridge_liveness.get("reviewer_mode")) or "tools_only"
    effective_mode = _text(bridge_liveness.get("effective_reviewer_mode")) or reviewer_mode
    participants = _build_participants(
        session_records,
        remote_attachments=remote_attachments,
    )
    role_assignments = _build_role_assignments(
        session_records,
        remote_attachments=remote_attachments,
        reviewer_mode=effective_mode,
    )
    participants, role_assignments = _promote_local_reviewer_presence(
        participants=participants,
        role_assignments=role_assignments,
        bridge_liveness=bridge_liveness,
        reviewer_mode=effective_mode,
        session_output_root=session_output_root,
    )
    participants, role_assignments = _promote_packet_active_implementer_presence(
        participants=participants,
        role_assignments=role_assignments,
        session_output_root=session_output_root,
    )
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
    current_slice = current_session.current_instruction or current_session.last_reviewed_scope
    ownership = build_collaboration_ownership(
        repo_root=repo_root,
        current_session=current_session,
        participants=participants,
        delegated_work=delegated_work,
        reviewer_mode=reviewer_mode,
        effective_mode=effective_mode,
    )
    mutation_owner = _agent_for_role(role_assignments, "coding_agent")
    verification_owner = _verification_owner(
        role_assignments=role_assignments,
        mutation_owner=mutation_owner,
    )
    verification_status = _owner_status(
        agent_id=verification_owner,
        participants=participants,
        role_assignments=role_assignments,
        preferred_role_ids=("review_agent", "operator_agent"),
    )
    watcher_owner = _watcher_owner(
        participants=participants,
        role_assignments=role_assignments,
        mutation_owner=mutation_owner,
        verification_owner=verification_owner,
    )
    watcher_status = _owner_status(
        agent_id=watcher_owner,
        participants=participants,
        role_assignments=role_assignments,
    )
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
        topology_mode=collaboration_topology_mode(
            reviewer_mode=effective_mode,
            participants=participants,
            delegated_work=delegated_work,
        ),
        work_ownership_mode=work_ownership_mode(ownership),
        ownership=ownership,
        mutation_owner=mutation_owner,
        verification_owner=verification_owner,
        verification_status=verification_status,
        watcher_owner=watcher_owner,
        watcher_status=watcher_status,
    )
def _promote_local_reviewer_presence(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    bridge_liveness: Mapping[str, object],
    reviewer_mode: str,
    session_output_root: Path | None,
) -> tuple[
    tuple[CollaborationParticipantState, ...],
    tuple[CollaborationRoleAssignmentState, ...],
]:
    _sync_local_reviewer_test_hooks()
    reviewer_provider = (
        _agent_for_role(role_assignments, "review_agent")
        or default_provider_for_role(TandemRole.REVIEWER)
    )
    if not reviewer_provider:
        return participants, role_assignments
    if not _local_reviewer.local_reviewer_turn_is_live(
        bridge_liveness=bridge_liveness,
        reviewer_mode=reviewer_mode,
        reviewer_provider=reviewer_provider,
        session_output_root=session_output_root,
    ):
        return participants, role_assignments

    session_name = _text(bridge_liveness.get("reviewer_session_name")) or (
        f"reviewer-local-{reviewer_provider}"
    )
    prepared_at = _text(bridge_liveness.get("last_reviewer_poll_utc")) or _text(
        bridge_liveness.get("last_codex_poll_utc")
    )
    updated_participants = list(participants)
    participant_live = False
    for index, participant in enumerate(updated_participants):
        if participant.provider != reviewer_provider:
            continue
        if participant.live:
            participant_live = True
            break
        updated_participants[index] = replace(
            participant,
            role=participant.role or TandemRole.REVIEWER.value,
            session_name=participant.session_name or session_name,
            live=True,
            status="live",
            capture_mode=participant.capture_mode or "local-reviewer",
            supervision_mode=participant.supervision_mode or "local-reviewer",
            prepared_at=participant.prepared_at or prepared_at,
        )
        participant_live = True
        break

    if not participant_live:
        updated_participants.append(
            CollaborationParticipantState(
                agent_id=reviewer_provider,
                provider=reviewer_provider,
                display_name=reviewer_provider.title(),
                role=TandemRole.REVIEWER.value,
                session_name=session_name,
                live=True,
                status="live",
                capture_mode="local-reviewer",
                supervision_mode="local-reviewer",
                prepared_at=prepared_at,
            )
        )

    updated_assignments = list(role_assignments)
    for index, assignment in enumerate(updated_assignments):
        if assignment.provider != reviewer_provider:
            continue
        if assignment.role_id not in {"lead_agent", "review_agent"} and not (
            reviewer_mode == "single_agent" and assignment.role_id == "coding_agent"
        ):
            continue
        if assignment.live:
            continue
        updated_assignments[index] = replace(
            assignment,
            status="live",
            source="reviewer_turn",
            session_name=session_name,
            live=True,
    )
    return tuple(updated_participants), tuple(updated_assignments)


def _promote_packet_active_implementer_presence(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    session_output_root: Path | None,
) -> tuple[
    tuple[CollaborationParticipantState, ...],
    tuple[CollaborationRoleAssignmentState, ...],
]:
    implementer_providers = tuple(
        assignment.provider
        for assignment in role_assignments
        if assignment.role_id == "coding_agent" and assignment.provider
    )
    if not implementer_providers or session_output_root is None:
        return participants, role_assignments

    active_providers = {
        provider
        for provider in implementer_providers
        if _provider_packet_activity_is_fresh(
            provider=provider,
            session_output_root=session_output_root,
        )
    }
    if not active_providers:
        return participants, role_assignments

    updated_participants = list(participants)
    for index, participant in enumerate(updated_participants):
        if participant.provider not in active_providers or participant.live:
            continue
        updated_participants[index] = replace(
            participant,
            live=True,
            status="live",
            capture_mode=participant.capture_mode or "packet-activity",
            supervision_mode=participant.supervision_mode or "packet-activity",
            session_name=participant.session_name or f"{participant.provider}-packet-activity",
            prepared_at=participant.prepared_at or _utcnow().isoformat(),
        )

    updated_assignments = list(role_assignments)
    for index, assignment in enumerate(updated_assignments):
        if (
            assignment.role_id != "coding_agent"
            or assignment.provider not in active_providers
            or assignment.live
        ):
            continue
        updated_assignments[index] = replace(
            assignment,
            status="live",
            source="packet_activity",
            session_name=assignment.session_name or f"{assignment.provider}-packet-activity",
            live=True,
        )

    return tuple(updated_participants), tuple(updated_assignments)


def _sync_local_reviewer_test_hooks() -> None:
    _local_reviewer._utcnow = _utcnow
    _local_reviewer.discover_latest_session = discover_latest_session
    _local_reviewer.local_reviewer_activity_is_fresh = _local_reviewer_activity_is_fresh
