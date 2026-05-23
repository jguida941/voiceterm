"""Presence-promotion helpers for collaboration-session state."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path

from ..runtime.review_state_models import (
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
)
from ..runtime.role_profile import role_capability_classes
from . import collaboration_session_local_reviewer as _local_reviewer


def promote_local_reviewer_presence(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    bridge_liveness: Mapping[str, object],
    reviewer_mode: str,
    session_output_root: Path | None,
    utcnow: Callable[[], object],
    discover_latest_session: Callable[[str], Path | None],
    local_reviewer_activity_is_fresh: Callable[..., bool],
) -> tuple[
    tuple[CollaborationParticipantState, ...],
    tuple[CollaborationRoleAssignmentState, ...],
]:
    _sync_local_reviewer_test_hooks(
        utcnow=utcnow,
        discover_latest_session=discover_latest_session,
        local_reviewer_activity_is_fresh=local_reviewer_activity_is_fresh,
    )
    reviewer_provider = _provider_for_capability(
        role_assignments,
        {"review", "architecture", "governance", "research", "test", "intake"},
    ) or _text(bridge_liveness.get("reviewer_activity_provider"))
    if not reviewer_provider:
        return participants, role_assignments
    reviewer_role = _role_for_provider(
        role_assignments,
        reviewer_provider,
        {"review", "architecture", "governance", "research", "test", "intake"},
    ) or "architecture_review"
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
            role=participant.role or reviewer_role,
            session_name=participant.session_name or session_name,
            live=True,
            status="live",
            capture_mode=participant.capture_mode or "local-reviewer",
            supervision_mode=participant.supervision_mode or "local-reviewer",
            prepared_at=participant.prepared_at or prepared_at,
            host_wake_mode="continuous",
            host_wake_summary=participant.host_wake_summary
            or "Repo-owned reviewer lane is wake-capable.",
        )
        participant_live = True
        break

    if not participant_live:
        updated_participants.append(
            CollaborationParticipantState(
                agent_id=reviewer_provider,
                provider=reviewer_provider,
                display_name=reviewer_provider.title(),
                role=reviewer_role,
                session_name=session_name,
                live=True,
                status="live",
                capture_mode="local-reviewer",
                supervision_mode="local-reviewer",
                prepared_at=prepared_at,
                host_wake_mode="continuous",
                host_wake_summary="Repo-owned reviewer lane is wake-capable.",
            )
        )

    updated_assignments = list(role_assignments)
    single_agent_mode = reviewer_mode == "single_agent"
    for index, assignment in enumerate(updated_assignments):
        if assignment.provider != reviewer_provider:
            continue
        review_lane = _role_has_capability(
            assignment.role_id,
            {"review", "architecture", "governance", "research", "test", "intake"},
        )
        single_agent_coding_lane = single_agent_mode and _role_has_capability(
            assignment.role_id,
            {"implementation", "mutation"},
        )
        if not review_lane and not single_agent_coding_lane:
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


def promote_packet_active_implementer_presence(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    reviewer_mode: str,
    session_output_root: Path | None,
    utcnow: Callable[[], object],
    provider_packet_activity_is_fresh: Callable[..., bool],
) -> tuple[
    tuple[CollaborationParticipantState, ...],
    tuple[CollaborationRoleAssignmentState, ...],
]:
    if reviewer_mode == "single_agent":
        return participants, role_assignments
    implementer_providers = tuple(
        assignment.provider
        for assignment in role_assignments
        if assignment.provider
        and _role_has_capability(assignment.role_id, {"implementation", "mutation"})
    )
    if not implementer_providers or session_output_root is None:
        return participants, role_assignments

    active_providers = {
        provider
        for provider in implementer_providers
        if provider_packet_activity_is_fresh(
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
            prepared_at=participant.prepared_at or utcnow().isoformat(),
            host_wake_mode=(
                "unknown"
                if participant.host_wake_mode in {"", "inactive"}
                else participant.host_wake_mode
            ),
            host_wake_summary=participant.host_wake_summary
            or "Packet activity was observed, but host wake capability is not typed.",
        )

    updated_assignments = list(role_assignments)
    for index, assignment in enumerate(updated_assignments):
        if (
            assignment.provider not in active_providers
            or not _role_has_capability(
                assignment.role_id,
                {"implementation", "mutation"},
            )
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


def _sync_local_reviewer_test_hooks(
    *,
    utcnow: Callable[[], object],
    discover_latest_session: Callable[[str], Path | None],
    local_reviewer_activity_is_fresh: Callable[..., bool],
) -> None:
    _local_reviewer._utcnow = utcnow
    _local_reviewer.discover_latest_session = discover_latest_session
    _local_reviewer.local_reviewer_activity_is_fresh = local_reviewer_activity_is_fresh


def _text(value: object) -> str:
    return str(value or "").strip()


def _provider_for_capability(
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    capability_classes: set[str],
) -> str:
    for assignment in role_assignments:
        if not assignment.provider:
            continue
        if _role_has_capability(assignment.role_id, capability_classes):
            return assignment.provider
    return ""


def _role_for_provider(
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    provider: str,
    capability_classes: set[str],
) -> str:
    for assignment in role_assignments:
        if assignment.provider != provider:
            continue
        if _role_has_capability(assignment.role_id, capability_classes):
            return assignment.role_id
    return ""


def _role_has_capability(role_id: str, capability_classes: set[str]) -> bool:
    return bool(set(role_capability_classes(role_id)) & capability_classes)
