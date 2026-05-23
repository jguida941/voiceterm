"""Shared collaboration-owner selection helpers."""

from __future__ import annotations

from .review_state_models import CollaborationRoleAssignmentState
from .role_profile import role_capability_classes


def select_verification_owner(
    *,
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    mutation_owner: str,
    same_agent_fn,
) -> str:
    """Pick the first non-mutation review/operator owner candidate."""
    for assignment in role_assignments:
        if not assignment.agent_id:
            continue
        if same_agent_fn(assignment.agent_id, mutation_owner):
            continue
        capability_classes = set(role_capability_classes(assignment.role_id))
        if capability_classes & {
            "review",
            "test",
            "architecture",
            "governance",
            "research",
            "intake",
            "control",
            "observe",
        }:
            return assignment.agent_id
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
