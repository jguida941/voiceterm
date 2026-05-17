"""Shared collaboration-owner selection helpers."""

from __future__ import annotations

from .review_state_models import CollaborationRoleAssignmentState


def select_verification_owner(
    *,
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    mutation_owner: str,
    same_agent_fn,
) -> str:
    """Pick the first non-mutation review/operator owner candidate."""
    for role_id in ("review_agent", "operator_agent"):
        agent_id = agent_for_role(role_assignments, role_id)
        if agent_id and not same_agent_fn(agent_id, mutation_owner):
            return agent_id
    return ""


def agent_for_role(
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    role_id: str,
) -> str:
    """Return the assigned agent for the requested role id."""
    for assignment in role_assignments:
        if assignment.role_id == role_id:
            return assignment.agent_id
    return ""
