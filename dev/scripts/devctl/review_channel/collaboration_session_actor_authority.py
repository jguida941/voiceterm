"""Actor-authority grant projection for collaboration sessions."""

from __future__ import annotations

from dataclasses import dataclass

from ..runtime.review_state_collaboration_models import ActorAuthorityState
from ..runtime.review_state_models import (
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
)
from .collaboration_session_actor_grants import authority_grants, worktree_identity
from .collaboration_session_actor_order import ordered_actor_ids
from .collaboration_session_actor_roles import authority_role, preferred_assignment
from .collaboration_session_lane_owners import owner_status, same_agent


@dataclass(frozen=True, slots=True)
class ActorAuthorityBuildInputs:
    participants: tuple[CollaborationParticipantState, ...]
    role_assignments: tuple[CollaborationRoleAssignmentState, ...]
    reviewer_mode: str
    mutation_owner: str
    verification_owner: str
    watcher_owner: str
    timestamp: str


@dataclass(frozen=True, slots=True)
class _ActorAuthorityContext:
    inputs: ActorAuthorityBuildInputs
    actor_id: str
    participant: CollaborationParticipantState | None
    assignment: CollaborationRoleAssignmentState | None
    role: str
    status: str
    live: bool


def actor_authorities(
    inputs: ActorAuthorityBuildInputs,
) -> tuple[ActorAuthorityState, ...]:
    """Build identity-bound authority rows for all observed actors."""
    rows: list[ActorAuthorityState] = []
    for actor_id in ordered_actor_ids(inputs):
        context = _authority_context(inputs, actor_id)
        rows.append(
            ActorAuthorityState(
                actor_id=actor_id,
                provider=_authority_provider(context),
                role=context.role,
                live=context.live,
                status=context.status,
                source=_authority_source(context),
                grants=authority_grants(context),
                session_id=_authority_session_id(context),
                source_identity={
                    "reviewer_mode": inputs.reviewer_mode,
                    "mutation_owner": inputs.mutation_owner,
                    "verification_owner": inputs.verification_owner,
                    "watcher_owner": inputs.watcher_owner,
                },
                worktree_identity=worktree_identity(context.participant),
                issued_at_utc=inputs.timestamp,
            )
        )
    return tuple(rows)


def _authority_context(
    inputs: ActorAuthorityBuildInputs,
    actor_id: str,
) -> _ActorAuthorityContext:
    participant = _participant_for_actor(inputs.participants, actor_id)
    assignment = preferred_assignment(inputs, actor_id)
    role = authority_role(
        inputs=inputs,
        assignment=assignment,
        participant=participant,
        actor_id=actor_id,
    )
    status = owner_status(
        agent_id=actor_id,
        participants=inputs.participants,
        role_assignments=inputs.role_assignments,
    )
    return _ActorAuthorityContext(
        inputs=inputs,
        actor_id=actor_id,
        participant=participant,
        assignment=assignment,
        role=role,
        status=status,
        live=status == "live",
    )


def _participant_for_actor(
    participants: tuple[CollaborationParticipantState, ...],
    actor_id: str,
) -> CollaborationParticipantState | None:
    for participant in participants:
        if same_agent(participant.agent_id or participant.provider, actor_id):
            return participant
    return None


def _authority_provider(context: _ActorAuthorityContext) -> str:
    if context.participant is not None:
        return (
            context.participant.provider
            or context.participant.agent_id
            or context.actor_id
        )
    if context.assignment is not None:
        return (
            context.assignment.provider
            or context.assignment.agent_id
            or context.actor_id
        )
    return context.actor_id


def _authority_source(context: _ActorAuthorityContext) -> str:
    if context.participant is not None and context.participant.capture_mode:
        return context.participant.capture_mode
    if context.assignment is not None:
        return context.assignment.source
    return "collaboration_session"


def _authority_session_id(context: _ActorAuthorityContext) -> str:
    if context.participant is not None:
        return context.participant.session_name
    if context.assignment is not None:
        return context.assignment.session_name
    return ""
