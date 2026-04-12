"""Builders for the typed collaboration-session review-state contract."""

from __future__ import annotations

import json
from collections import deque
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from ..commands.rollout_tail.discovery import discover_latest_session
from ..runtime.review_state_models import (
    CollaborationParticipantState,
    CollaborationPeerReviewState,
    CollaborationRoleAssignmentState,
    CollaborationSessionState,
    ReviewCurrentSessionState,
)
from ..runtime.role_profile import TandemRole, default_provider_for_role
from .peer_liveness import (
    CODEX_POLL_STALE_AFTER_SECONDS,
    ReviewerFreshness,
    classify_reviewer_freshness,
)
from .collaboration_session_roster import (
    _build_delegated_work,
    _build_participants,
    _build_role_assignments,
    _text,
)
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
from .session_probe import ConductorSessionRecord, load_conductor_sessions

_LOCAL_REVIEWER_EVENT_SCAN_LIMIT = 200
_LOCAL_REVIEWER_ACTIVITY_EVENT_TYPES = frozenset(
    {"packet_posted", "packet_acked", "packet_dismissed", "packet_applied"}
)


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
    participants = _build_participants(
        session_records,
        remote_attachments=remote_attachments,
    )
    role_assignments = _build_role_assignments(
        session_records,
        remote_attachments=remote_attachments,
    )
    reviewer_mode = _text(bridge_liveness.get("reviewer_mode")) or "tools_only"
    effective_mode = _text(bridge_liveness.get("effective_reviewer_mode")) or reviewer_mode
    participants, role_assignments = _promote_local_reviewer_presence(
        participants=participants,
        role_assignments=role_assignments,
        bridge_liveness=bridge_liveness,
        reviewer_mode=effective_mode,
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
    reviewer_provider = (
        _agent_for_role(role_assignments, "review_agent")
        or default_provider_for_role(TandemRole.REVIEWER)
    )
    if not reviewer_provider:
        return participants, role_assignments
    if not _local_reviewer_turn_is_live(
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
        if assignment.role_id not in {"lead_agent", "review_agent"}:
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


def _local_reviewer_turn_is_live(
    *,
    bridge_liveness: Mapping[str, object],
    reviewer_mode: str,
    reviewer_provider: str,
    session_output_root: Path | None,
) -> bool:
    if reviewer_mode != "single_agent":
        return False
    freshness = _text(bridge_liveness.get("reviewer_freshness"))
    if freshness in {"fresh", "poll_due"}:
        return True
    if _text(bridge_liveness.get("reviewer_poll_state")) in {"fresh", "poll_due"}:
        return True
    if _text(bridge_liveness.get("codex_poll_state")) in {"fresh", "poll_due"}:
        return True
    return _local_reviewer_activity_is_fresh(
        reviewer_provider=reviewer_provider,
        session_output_root=session_output_root,
    )


def _local_reviewer_activity_is_fresh(
    *,
    reviewer_provider: str,
    session_output_root: Path | None,
) -> bool:
    event_log_path = _resolve_event_log_path(session_output_root)
    if event_log_path is not None:
        latest_activity = _latest_local_reviewer_activity(
            event_log_path,
            reviewer_provider=reviewer_provider,
        )
        if latest_activity is not None:
            activity_age = _age_seconds(str(latest_activity.get("timestamp_utc") or ""))
            freshness = classify_reviewer_freshness(activity_age)
            if freshness not in {ReviewerFreshness.MISSING, ReviewerFreshness.OVERDUE}:
                return True
    return _local_reviewer_rollout_is_fresh(reviewer_provider=reviewer_provider)


def _local_reviewer_rollout_is_fresh(*, reviewer_provider: str) -> bool:
    rollout_path = _latest_local_reviewer_rollout_path(
        reviewer_provider=reviewer_provider
    )
    if rollout_path is None:
        return False
    try:
        modified_at = datetime.fromtimestamp(rollout_path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return False
    age_seconds = int(max((_utcnow() - modified_at).total_seconds(), 0.0))
    return age_seconds <= CODEX_POLL_STALE_AFTER_SECONDS


def _latest_local_reviewer_rollout_path(*, reviewer_provider: str) -> Path | None:
    provider = _text(reviewer_provider)
    if not provider:
        return None
    return discover_latest_session(provider)


def _resolve_event_log_path(session_output_root: Path | None) -> Path | None:
    if session_output_root is None:
        return None
    candidates = (
        session_output_root / "events/trace.ndjson",
        session_output_root.parent / "events/trace.ndjson",
        session_output_root.parent.parent / "events/trace.ndjson",
    )
    for path in candidates:
        if path.is_file():
            return path
    return None


def _latest_local_reviewer_activity(
    event_log_path: Path,
    *,
    reviewer_provider: str,
) -> dict[str, object] | None:
    for event in reversed(_load_recent_event_rows(event_log_path)):
        if _event_marks_local_reviewer_activity(
            event,
            reviewer_provider=reviewer_provider,
        ):
            return event
    return None


def _load_recent_event_rows(event_log_path: Path) -> list[dict[str, object]]:
    try:
        with event_log_path.open(encoding="utf-8") as handle:
            lines = list(deque(handle, maxlen=_LOCAL_REVIEWER_EVENT_SCAN_LIMIT))
    except OSError:
        return []
    events: list[dict[str, object]] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _event_marks_local_reviewer_activity(
    event: Mapping[str, object],
    *,
    reviewer_provider: str,
) -> bool:
    event_type = str(event.get("event_type") or "").strip()
    if event_type not in _LOCAL_REVIEWER_ACTIVITY_EVENT_TYPES:
        return False
    if event_type == "packet_posted":
        return _text(event.get("from_agent")) == reviewer_provider
    metadata = event.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    return _text(metadata.get("actor")) == reviewer_provider


def _age_seconds(timestamp_utc: str) -> int | None:
    text = timestamp_utc.strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        observed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    return int(max((_utcnow() - observed.astimezone(timezone.utc)).total_seconds(), 0.0))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
