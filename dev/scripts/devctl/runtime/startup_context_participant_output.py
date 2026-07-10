"""Startup projections for collaboration participants."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from .review_state_collaboration_models import (
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
)


def startup_role_assignment_dict(
    row: CollaborationRoleAssignmentState,
) -> dict[str, object]:
    return asdict(row)


def startup_participant_dict(row: CollaborationParticipantState) -> dict[str, object]:
    return _select(asdict(row), _PARTICIPANT_FIELDS)


def startup_participant_summary_dict(
    row: CollaborationParticipantState,
) -> dict[str, object]:
    return _select(asdict(row), _PARTICIPANT_SUMMARY_FIELDS)


def _select(
    row: Mapping[str, object],
    fields: tuple[str, ...],
) -> dict[str, object]:
    return {field: row.get(field, "") for field in fields}


_PARTICIPANT_FIELDS = (
    "agent_id",
    "provider",
    "display_name",
    "role",
    "session_name",
    "live",
    "status",
    "capture_mode",
    "approval_mode",
    "supervision_mode",
    "host_wake_mode",
    "wake_interval_seconds",
    "lane",
    "mp_scope",
    "worktree",
    "branch",
    "workspace_root",
)

_PARTICIPANT_SUMMARY_FIELDS = (
    "agent_id",
    "provider",
    "role",
    "live",
    "capture_mode",
)


__all__ = [
    "startup_participant_dict",
    "startup_participant_summary_dict",
    "startup_role_assignment_dict",
]
