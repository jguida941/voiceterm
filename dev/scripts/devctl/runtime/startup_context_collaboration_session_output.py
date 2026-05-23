"""Startup projections for collaboration session state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from .review_state_collaboration_models import CollaborationSessionState
from .startup_context_actor_authority_output import startup_actor_authority_dict
from .startup_context_participant_output import (
    startup_participant_dict,
    startup_participant_summary_dict,
    startup_role_assignment_dict,
)


def startup_collaboration_dict(
    collaboration: CollaborationSessionState,
) -> dict[str, object]:
    """Compact collaboration authority projection for startup-context."""
    payload = _select(asdict(collaboration), _COLLABORATION_FULL_FIELDS)
    payload["role_assignments"] = [
        startup_role_assignment_dict(row) for row in collaboration.role_assignments
    ]
    payload["participants"] = [
        startup_participant_dict(row) for row in collaboration.participants
    ]
    payload["actor_authorities"] = [
        startup_actor_authority_dict(row) for row in collaboration.actor_authorities
    ]
    return payload


def startup_collaboration_summary_dict(
    collaboration: CollaborationSessionState,
) -> dict[str, object]:
    """Final startup output keeps topology visible without duplicating grants."""
    payload = _collaboration_base(collaboration)
    payload["participants"] = [
        startup_participant_summary_dict(row) for row in collaboration.participants
    ]
    payload["role_assignments"] = [
        startup_role_assignment_dict(row) for row in collaboration.role_assignments
    ]
    return payload


def _collaboration_base(
    collaboration: CollaborationSessionState,
) -> dict[str, object]:
    return _select(asdict(collaboration), _COLLABORATION_BASE_FIELDS)


def _select(
    row: Mapping[str, object],
    fields: tuple[str, ...],
) -> dict[str, object]:
    return {field: row.get(field, "") for field in fields}


_COLLABORATION_BASE_FIELDS = (
    "schema_version",
    "contract_id",
    "session_id",
    "topology_mode",
    "mutation_owner",
    "verification_owner",
    "watcher_owner",
)

_COLLABORATION_FULL_FIELDS = (
    *_COLLABORATION_BASE_FIELDS,
    "reviewer_mode",
    "operator_mode",
    "status",
    "current_slice",
    "verification_status",
    "watcher_status",
    "mutation_wake_mode",
    "verification_wake_mode",
    "watcher_wake_mode",
    "wake_continuity_ok",
    "wake_gap_summary",
    "loop_wake_mode",
    "loop_wake_interval_seconds",
    "loop_driver_agent",
    "loop_autonomy_ok",
    "loop_gap_summary",
)


__all__ = [
    "startup_collaboration_dict",
    "startup_collaboration_summary_dict",
]
