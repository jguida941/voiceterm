"""Coordination helpers for typed startup action routing."""

from __future__ import annotations

from collections.abc import Mapping

from .reviewer_mode_projection import (
    write_effective_reviewer_mode,
    write_reviewer_mode,
)
from .work_intake_models import (
    WorkIntakeCoordinationState,
    work_intake_coordination_from_mapping,
)


def coordination_state(
    ctx_payload: Mapping[str, object],
) -> WorkIntakeCoordinationState | None:
    """Resolve typed coordination for action-routing from shared payload shapes."""
    work_intake = _mapping(ctx_payload.get("work_intake"))
    work_intake_coordination = work_intake_coordination_from_mapping(
        work_intake.get("coordination")
    )
    if work_intake_coordination is not None:
        return work_intake_coordination

    coordination = _mapping(ctx_payload.get("coordination"))
    if not coordination:
        return None

    projected = dict(coordination)
    if not projected.get("implementation_permission"):
        implementation_permission = str(
            ctx_payload.get("implementation_permission") or ""
        ).strip()
        if implementation_permission:
            projected["implementation_permission"] = implementation_permission
    if not projected.get("reviewer_mode"):
        reviewer_mode = str(ctx_payload.get("reviewer_mode") or "").strip()
        if reviewer_mode:
            write_reviewer_mode(projected, reviewer_mode)
    if not projected.get("effective_reviewer_mode"):
        effective_mode = str(
            ctx_payload.get("effective_reviewer_mode")
            or ctx_payload.get("reviewer_mode")
            or ""
        ).strip()
        if effective_mode:
            write_effective_reviewer_mode(projected, effective_mode)
    return work_intake_coordination_from_mapping(projected)


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
