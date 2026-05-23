"""Support helpers for legacy collaboration-state fallback assembly."""

from __future__ import annotations

from .review_state_models import (
    AgentRegistryState,
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
    ConductorCapabilityState,
)
from .role_profile import normalize_role_id, role_capability_classes


def legacy_agent_for_role(
    assignments: tuple[CollaborationRoleAssignmentState, ...],
    role_id: str,
) -> str:
    for assignment in assignments:
        if assignment.role_id == role_id:
            return assignment.agent_id
    return ""


def legacy_watcher_owner(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
    mutation_owner: str,
    verification_owner: str,
) -> str:
    operator_owner = legacy_agent_for_capability(
        role_assignments,
        {"control", "observe"},
    )
    for candidate in (operator_owner, mutation_owner, verification_owner):
        if legacy_owner_status(
            candidate,
            participants=participants,
            role_assignments=role_assignments,
        ) == "live":
            return candidate
    for candidate in (operator_owner, mutation_owner, verification_owner):
        if legacy_owner_status(
            candidate,
            participants=participants,
            role_assignments=role_assignments,
        ) != "inactive":
            return candidate
    return ""


def legacy_agent_for_capability(
    assignments: tuple[CollaborationRoleAssignmentState, ...],
    capability_classes: set[str],
    *,
    excluded_agent_id: str = "",
) -> str:
    for assignment in assignments:
        if not assignment.agent_id:
            continue
        if excluded_agent_id and same_agent(assignment.agent_id, excluded_agent_id):
            continue
        if set(role_capability_classes(assignment.role_id)) & capability_classes:
            return assignment.agent_id
    return ""


def legacy_owner_status(
    agent_id: str,
    *,
    participants: tuple[CollaborationParticipantState, ...],
    role_assignments: tuple[CollaborationRoleAssignmentState, ...],
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
        if assignment.live:
            return "live"
        if assignment.status:
            return assignment.status
    return "inactive"


def same_agent(left: str, right: str) -> bool:
    return bool(left and right and left.strip().lower() == right.strip().lower())


def provider_from_registry(
    registry: AgentRegistryState,
    role_name: str,
) -> str:
    for agent in registry.agents:
        provider = agent.provider or agent.agent_id
        role_id = normalize_role_id(agent.lane or agent.current_job)
        if role_id == role_name:
            return provider
    return ""


def capability_provider(
    capability: ConductorCapabilityState | None,
    *,
    default: str,
) -> str:
    provider = capability.provider if capability is not None else ""
    return provider.strip() or default
