"""Derived mutation/verifier/watcher ownership for collaboration sessions."""

from __future__ import annotations

from ..runtime.collaboration_owner_selection import select_verification_owner
from ..runtime.review_state_models import (
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
)
from .collaboration_session_status import _agent_for_role

_WATCHER_CAPTURE_MODES = frozenset({"packet-activity", "packet-watch", "remote-control"})


def verification_owner(
    *,
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    mutation_owner: str,
) -> str:
    return select_verification_owner(
        role_assignments=role_assignments,
        mutation_owner=mutation_owner,
        same_agent_fn=same_agent,
    )


def watcher_owner(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    mutation_owner: str,
    verification_owner: str,
) -> str:
    operator_owner = _agent_for_role(role_assignments, "operator_agent")
    candidates: list[str] = []
    if operator_owner:
        candidates.append(operator_owner)
    for participant in participants:
        if participant.capture_mode not in _WATCHER_CAPTURE_MODES:
            continue
        candidate = participant.agent_id or participant.provider
        if candidate:
            candidates.append(candidate)
    if mutation_owner:
        candidates.append(mutation_owner)
    if verification_owner:
        candidates.append(verification_owner)

    for candidate in candidates:
        if owner_status(
            agent_id=candidate,
            participants=participants,
            role_assignments=role_assignments,
        ) == "live":
            return candidate
    for candidate in candidates:
        if owner_status(
            agent_id=candidate,
            participants=participants,
            role_assignments=role_assignments,
        ) != "inactive":
            return candidate
    return ""


def owner_status(
    *,
    agent_id: str,
    participants: tuple[CollaborationParticipantState, ...],
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    preferred_role_ids: tuple[str, ...] = (),
) -> str:
    if not agent_id:
        return "inactive"
    for participant in participants:
        if not same_agent(participant.agent_id or participant.provider, agent_id):
            continue
        if participant.live:
            return "live"
        if participant.status:
            return participant.status
    for assignment in role_assignments:
        if not same_agent(assignment.agent_id or assignment.provider, agent_id):
            continue
        if preferred_role_ids and assignment.role_id not in preferred_role_ids:
            continue
        if assignment.live:
            return "live"
        if assignment.status:
            return assignment.status
    return "inactive"


def same_agent(left: str, right: str) -> bool:
    return bool(left and right and left.strip().lower() == right.strip().lower())
