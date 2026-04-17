"""Shared command strings and guidance for governed commit preflight."""

from __future__ import annotations

from ...runtime.operator_context import (
    OperatorInteractionMode,
    resolve_operator_interaction_mode,
)

COMMIT_START_COMMAND = 'python3 dev/scripts/devctl.py commit -m "<descriptive message>"'
APPROVE_PENDING_COMMAND = (
    "python3 dev/scripts/devctl.py commit --approve-pending --format json"
)
OPERATOR_INBOX_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action operator-inbox "
    "--status pending --terminal none --format json"
)
OPERATOR_HISTORY_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action history "
    "--target operator --limit 5 --terminal none --format json"
)


def next_command_guidance(next_command: str) -> str:
    """Render operator guidance directly from a typed next command."""
    if not next_command:
        return ""
    return f"Run `{next_command}` next."


def should_auto_approve(interaction_mode: str) -> bool:
    """Return True when the current operator mode can self-approve locally."""
    mode = resolve_operator_interaction_mode(str(interaction_mode or "").strip()).value
    return mode in {
        OperatorInteractionMode.LOCAL_TERMINAL.value,
        OperatorInteractionMode.SINGLE_AGENT.value,
    }
