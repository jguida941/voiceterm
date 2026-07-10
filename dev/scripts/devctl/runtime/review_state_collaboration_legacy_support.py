"""Support helpers for legacy collaboration-state fallback assembly."""

from __future__ import annotations

from .review_state_models import (
    AgentRegistryState,
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
    ConductorCapabilityState,
)
from .role_profile import TandemRole, default_provider_for_role, normalize_tandem_role, role_for_provider


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
    operator_owner = legacy_agent_for_role(role_assignments, "operator_agent")
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
        if (
            normalized_job := normalize_tandem_role(agent.current_job)
        ) is not None and normalized_job.value == role_name:
            return provider
        if role_for_provider(provider).value == role_name:
            return provider
    return ""


def capability_provider(
    capability: ConductorCapabilityState | None,
    *,
    default: str,
) -> str:
    provider = capability.provider if capability is not None else ""
    return provider.strip() or default
