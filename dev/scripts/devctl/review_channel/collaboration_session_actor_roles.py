"""Actor-role resolution helpers for collaboration-session authority rows."""

from __future__ import annotations

from ..runtime.review_state_models import (
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
)
from .collaboration_session_lane_owners import same_agent


def preferred_assignment(
    inputs: object,
    actor_id: str,
) -> CollaborationRoleAssignmentState | None:
    preferred_role_ids = _preferred_role_ids(inputs, actor_id)
    for role_id in preferred_role_ids:
        for assignment in inputs.role_assignments:
            if assignment.role_id == role_id and same_agent(
                assignment.agent_id or assignment.provider,
                actor_id,
            ):
                return assignment
    return None


def authority_role(
    *,
    inputs: object,
    assignment: CollaborationRoleAssignmentState | None,
    participant: CollaborationParticipantState | None,
    actor_id: str,
) -> str:
    if same_agent(actor_id, inputs.mutation_owner):
        return "implementer"
    if same_agent(actor_id, inputs.verification_owner):
        return "reviewer"
    if assignment is not None:
        if assignment.role_id == "operator_agent":
            return "operator"
        if assignment.role_id == "coding_agent":
            return "implementer"
        if assignment.role_id in {"review_agent", "lead_agent"}:
            return "reviewer"
    if participant is not None and participant.role:
        return participant.role
    return "unknown"


def _preferred_role_ids(inputs: object, actor_id: str) -> tuple[str, ...]:
    if same_agent(actor_id, inputs.mutation_owner):
        return ("coding_agent", "review_agent", "lead_agent")
    if same_agent(actor_id, inputs.verification_owner):
        return ("review_agent", "operator_agent", "lead_agent")
    return ("operator_agent", "coding_agent", "review_agent", "lead_agent")
