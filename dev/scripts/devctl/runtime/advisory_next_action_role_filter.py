"""Role-aware projection for advisory next-command surfaces."""

from __future__ import annotations

READ_ONLY_NEXT_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)
READ_ONLY_ADVISORY_ROLES = frozenset({"dashboard", "observer"})
MUTATING_NEXT_COMMAND_MARKERS = (
    " dev/scripts/devctl.py commit",
    " dev/scripts/devctl.py push",
    " dev/scripts/devctl.py pipeline --action",
    " git add",
    " git commit",
    " git push",
)


def advisory_role_is_read_only(role: object) -> bool:
    """Return True when the caller role must not receive mutating commands."""
    return str(role or "").strip().lower() in READ_ONLY_ADVISORY_ROLES


def command_requests_mutation(command: object) -> bool:
    """Return True when a next-command string asks for a repo mutation."""
    normalized = f" {str(command or '').strip()}"
    return any(marker in normalized for marker in MUTATING_NEXT_COMMAND_MARKERS)


def project_next_command_for_role(*, role: object, command: object) -> str:
    """Return the role-visible next command for advisory read surfaces."""
    projected = str(command or "").strip()
    if advisory_role_is_read_only(role) and command_requests_mutation(projected):
        return READ_ONLY_NEXT_COMMAND
    return projected


__all__ = [
    "MUTATING_NEXT_COMMAND_MARKERS",
    "READ_ONLY_ADVISORY_ROLES",
    "READ_ONLY_NEXT_COMMAND",
    "advisory_role_is_read_only",
    "command_requests_mutation",
    "project_next_command_for_role",
]
