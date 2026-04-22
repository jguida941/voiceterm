"""Role-specific projections for session-resume command fields."""

from __future__ import annotations

READ_ONLY_NEXT_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)
READ_ONLY_SESSION_ROLES = frozenset({"dashboard", "observer"})
MUTATING_NEXT_COMMAND_MARKERS = (
    " dev/scripts/devctl.py commit",
    " dev/scripts/devctl.py push",
    " dev/scripts/devctl.py pipeline --action",
    " git add",
    " git commit",
    " git push",
)


def project_packet_next_command_for_role(*, role: str, command: str) -> str:
    """Return the role-visible next command for session-resume packet fields."""
    projected = str(command or "").strip()
    normalized_role = str(role or "").strip().lower()
    if normalized_role in READ_ONLY_SESSION_ROLES and _command_requests_mutation(
        projected
    ):
        return READ_ONLY_NEXT_COMMAND
    return projected


def _command_requests_mutation(command: str) -> bool:
    normalized = f" {command.strip()}"
    return any(marker in normalized for marker in MUTATING_NEXT_COMMAND_MARKERS)
