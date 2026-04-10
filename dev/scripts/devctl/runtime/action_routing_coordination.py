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
    """Resolve typed coordination for action-routing from the startup payload."""
    work_intake = _mapping(ctx_payload.get("work_intake"))
    typed_coordination = work_intake_coordination_from_mapping(
        work_intake.get("coordination")
    )
    if typed_coordination is not None:
        return typed_coordination
    return _coordination_state_from_snapshot(ctx_payload.get("coordination"))


def active_implementation_owner(
    coordination: WorkIntakeCoordinationState | None,
    ctx_payload: Mapping[str, object],
) -> str:
    """Resolve the active implementer, preferring typed work-intake state."""
    if coordination is not None:
        owner = str(coordination.active_implementation_owner or "").strip()
        if owner:
            return owner
        owner = _owner_from_active_participants(coordination.active_participants)
        if owner:
            return owner
    return _owner_from_snapshot(ctx_payload)


def _coordination_state_from_snapshot(
    value: object,
) -> WorkIntakeCoordinationState | None:
    coordination = _mapping(value)
    if not coordination:
        return None
    active_participants = tuple(
        str(item).strip()
        for item in coordination.get("active_participants", ())
        if str(item).strip()
    )
    return WorkIntakeCoordinationState(
        authority_mode=str(coordination.get("authority_mode") or "").strip()
        or "self_directed",
        work_ownership_mode=str(coordination.get("work_ownership_mode") or "").strip()
        or "exclusive_slice",
        sync_cadence_mode=str(coordination.get("sync_cadence_mode") or "").strip()
        or "continuous",
        collaboration_topology=str(
            coordination.get("observed_topology")
            or coordination.get("recommended_topology")
            or "single_agent"
        ).strip(),
        active_implementation_owner=_owner_from_active_participants(
            active_participants
        ),
        active_participants=active_participants,
        resync_required=bool(coordination.get("resync_required", False)),
    )


def _owner_from_active_participants(active_participants: tuple[str, ...]) -> str:
    for participant in active_participants:
        actor, _, role = str(participant or "").strip().partition(":")
        if role == "implementer" and actor:
            return actor
    return ""


def _owner_from_snapshot(ctx_payload: Mapping[str, object]) -> str:
    coordination = _mapping(ctx_payload.get("coordination"))
    actors = coordination.get("actors", ())
    if isinstance(actors, (list, tuple)):
        for actor in actors:
            if not isinstance(actor, Mapping):
                continue
            role = str(actor.get("role") or "").strip().lower()
            presence = str(actor.get("presence") or "").strip().lower()
            if role != "implementer" or presence not in {"live", "active"}:
                continue
            actor_id = str(
                actor.get("actor_id") or actor.get("provider") or ""
            ).strip()
            if actor_id:
                return actor_id
    active_participants = coordination.get("active_participants", ())
    if isinstance(active_participants, (list, tuple)):
        owner = _owner_from_active_participants(
            tuple(str(item or "").strip() for item in active_participants)
        )
        if owner:
            return owner
    return ""


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


__all__ = ["active_implementation_owner", "coordination_state"]
