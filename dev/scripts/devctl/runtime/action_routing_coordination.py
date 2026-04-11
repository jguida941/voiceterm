"""Coordination helpers for typed startup action routing."""

from __future__ import annotations

from collections.abc import Mapping

from .work_intake_models import (
    WorkIntakeCoordinationState,
    work_intake_coordination_from_mapping,
)


def coordination_state(
    ctx_payload: Mapping[str, object],
) -> WorkIntakeCoordinationState | None:
    """Resolve typed coordination for action-routing from work-intake only."""
    work_intake = _mapping(ctx_payload.get("work_intake"))
    return work_intake_coordination_from_mapping(work_intake.get("coordination"))


def active_implementation_owner(
    coordination: WorkIntakeCoordinationState | None,
) -> str:
    """Resolve the active implementer from the typed work-intake contract."""
    if coordination is not None:
        owner = str(coordination.active_implementation_owner or "").strip()
        if owner:
            return owner
        owner = _owner_from_active_participants(coordination.active_participants)
        if owner:
            return owner
    return ""


def _owner_from_active_participants(active_participants: tuple[str, ...]) -> str:
    for participant in active_participants:
        actor, _, role = str(participant or "").strip().partition(":")
        if role == "implementer" and actor:
            return actor
    return ""
def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


__all__ = ["active_implementation_owner", "coordination_state"]
