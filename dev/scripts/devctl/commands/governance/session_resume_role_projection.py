"""Role-specific projections for session-resume command fields."""

from __future__ import annotations

from ...runtime.advisory_next_action_role_filter import (
    MUTATING_NEXT_COMMAND_MARKERS,
    READ_ONLY_ADVISORY_ROLES,
    READ_ONLY_NEXT_COMMAND,
    command_requests_mutation,
    project_next_command_for_role,
)

READ_ONLY_SESSION_ROLES = READ_ONLY_ADVISORY_ROLES


def project_packet_next_command_for_role(*, role: str, command: str) -> str:
    """Return the role-visible next command for session-resume packet fields."""
    return project_next_command_for_role(role=role, command=command)


def _command_requests_mutation(command: str) -> bool:
    return command_requests_mutation(command)
