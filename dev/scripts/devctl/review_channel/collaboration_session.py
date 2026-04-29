"""Builders for the typed collaboration-session review-state contract."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..runtime.agent_session_outcome import projected_unresolved_session_outcomes
from ..runtime.review_state_models import (
    CollaborationPeerReviewState,
    CollaborationSessionState,
    ReviewCurrentSessionState,
)
from . import collaboration_session_local_reviewer as _local_reviewer
from .collaboration_session_actor_authority import (
    ActorAuthorityBuildInputs,
)
from .collaboration_session_actor_authority import (
    actor_authorities as _actor_authorities,
)
from .collaboration_session_coordination import (
    build_collaboration_ownership,
    collaboration_topology_mode,
    work_ownership_mode,
)
from .collaboration_session_lane_owners import owner_status as _owner_status
from .collaboration_session_lane_owners import verification_owner as _verification_owner
from .collaboration_session_lane_owners import watcher_owner as _watcher_owner
from .collaboration_session_presence import (
    promote_local_reviewer_presence,
    promote_packet_active_implementer_presence,
)
from .collaboration_session_roster import (
    _build_delegated_work,
    _build_participants,
    _build_role_assignments,
)
from .collaboration_session_status import (
    _agent_for_role,
    _build_arbitration,
    _build_ready_gates,
    _build_restart_state,
    _collaboration_status,
    _operator_mode,
)
from .agent_session_outcome_events import load_agent_session_outcomes
from .remote_control_attachment_artifact import load_remote_control_attachments
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
    session_records, remote_attachments = _load_runtime_session_rows(
        session_output_root=session_output_root,
    )
    session_outcomes = _build_session_outcomes(
        repo_root=repo_root,
        session_records=session_records,
        observed_at_utc=timestamp,
    )
    reviewer_mode = _text(bridge_liveness.get("reviewer_mode")) or "tools_only"
    effective_mode = (
        _text(bridge_liveness.get("effective_reviewer_mode")) or reviewer_mode
    )
    participants = _build_participants(
        session_records,
        remote_attachments=remote_attachments,
    )
    role_assignments = _build_role_assignments(
        session_records,
        remote_attachments=remote_attachments,
        reviewer_mode=effective_mode,
    )
    participants, role_assignments = promote_local_reviewer_presence(
        participants=participants,
        role_assignments=role_assignments,
        bridge_liveness=bridge_liveness,
        reviewer_mode=effective_mode,
        session_output_root=session_output_root,
        utcnow=_utcnow,
        discover_latest_session=discover_latest_session,
        local_reviewer_activity_is_fresh=_local_reviewer_activity_is_fresh,
    )
    participants, role_assignments = promote_packet_active_implementer_presence(
        participants=participants,
        role_assignments=role_assignments,
        session_output_root=session_output_root,
        utcnow=_utcnow,
        provider_packet_activity_is_fresh=_provider_packet_activity_is_fresh,
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
    current_slice = (
        current_session.current_instruction or current_session.last_reviewed_scope
    )
    ownership = build_collaboration_ownership(
        repo_root=repo_root,
        current_session=current_session,
        participants=participants,
        delegated_work=delegated_work,
        reviewer_mode=reviewer_mode,
        effective_mode=effective_mode,
    )
    (
        mutation_owner,
        verification_owner,
        verification_status,
        watcher_owner,
        watcher_status,
        authority_rows,
    ) = _collaboration_owner_fields(
        participants=participants,
        role_assignments=role_assignments,
        reviewer_mode=effective_mode,
        timestamp=timestamp,
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
        actor_authorities=authority_rows,
        session_outcomes=session_outcomes,
    )


def _load_runtime_session_rows(
    *,
    session_output_root: Path | None,
) -> tuple[tuple[object, ...], tuple[object, ...]]:
    if session_output_root is None:
        return (), ()
    return (
        load_conductor_sessions(session_output_root=session_output_root),
        load_remote_control_attachments(
            output_root=session_output_root,
            active_only=True,
        ),
    )


def _build_session_outcomes(
    *,
    repo_root: Path | None,
    session_records: tuple[object, ...],
    observed_at_utc: str,
) -> tuple[object, ...]:
    loaded_session_outcomes = _load_session_outcomes(repo_root=repo_root)
    return (
        *loaded_session_outcomes,
        *projected_unresolved_session_outcomes(
            session_records,
            loaded_session_outcomes,
            observed_at_utc=observed_at_utc,
        ),
    )


def _load_session_outcomes(
    *,
    repo_root: Path | None,
) -> tuple[object, ...]:
    if repo_root is None:
        return ()
    try:
        from .event_store import resolve_artifact_paths

        artifact_paths = resolve_artifact_paths(repo_root=repo_root)
        return load_agent_session_outcomes(
            events_path=Path(artifact_paths.event_log_path)
        )
    except (OSError, ValueError):
        return ()


def _collaboration_owner_fields(
    *,
    participants: object,
    role_assignments: object,
    reviewer_mode: str,
    timestamp: str,
) -> tuple[object, ...]:
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
    authority_rows = _actor_authorities(
        ActorAuthorityBuildInputs(
            participants=participants,
            role_assignments=role_assignments,
            reviewer_mode=reviewer_mode,
            mutation_owner=mutation_owner,
            verification_owner=verification_owner,
            watcher_owner=watcher_owner,
            timestamp=timestamp,
        )
    )
    return (
        mutation_owner,
        verification_owner,
        verification_status,
        watcher_owner,
        watcher_status,
        authority_rows,
    )


def _sync_local_reviewer_test_hooks() -> None:
    _local_reviewer._utcnow = _utcnow
    _local_reviewer.discover_latest_session = discover_latest_session
    _local_reviewer.local_reviewer_activity_is_fresh = _local_reviewer_activity_is_fresh
