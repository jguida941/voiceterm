"""Typed live-session posture for reviewer/runtime projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from .session_posture_build_support import (
    bool_value,
    collect_session_posture_actors,
    normalize_current_activity,
    normalize_occupied_lane as _normalize_occupied_lane,
    resolve_interaction_mode,
    string_rows,
)


@dataclass(frozen=True, slots=True)
class SessionPostureActor:
    """One actor's current occupied lane and separate granted capabilities."""

    actor_id: str = ""
    provider: str = ""
    role: str = ""
    occupied_lane: str = ""
    presence: str = ""
    live: bool = False
    source: str = ""
    activity_age_seconds: int = 0
    current_activity: str = "waiting"
    current_target: str = ""
    granted_capabilities: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["granted_capabilities"] = list(self.granted_capabilities)
        return payload


@dataclass(frozen=True, slots=True)
class SessionPosture:
    """Canonical live posture tuple for this proof tick."""

    schema_version: int = 1
    contract_id: str = "SessionPosture"
    interaction_mode: str = "unresolved"
    reviewer_mode: str = "single_agent"
    effective_reviewer_mode: str = "single_agent"
    actors: tuple[SessionPostureActor, ...] = ()
    source: str = "reviewer_runtime"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["actors"] = [actor.to_dict() for actor in self.actors]
        return payload


def session_posture_from_mapping(value: object) -> SessionPosture | None:
    """Deserialize a SessionPosture payload, returning None when absent."""
    if not isinstance(value, Mapping):
        return None
    actors = tuple(
        actor
        for actor in (
            session_posture_actor_from_mapping(item)
            for item in value.get("actors", ())
        )
        if actor is not None
    )
    if not actors and not str(value.get("interaction_mode") or "").strip():
        return None
    return SessionPosture(
        schema_version=int(value.get("schema_version") or 1),
        contract_id=str(value.get("contract_id") or "SessionPosture").strip(),
        interaction_mode=resolve_interaction_mode(value.get("interaction_mode")),
        reviewer_mode=_text(value.get("reviewer_mode")) or "single_agent",
        effective_reviewer_mode=(
            _text(value.get("effective_reviewer_mode"))
            or _text(value.get("reviewer_mode"))
            or "single_agent"
        ),
        actors=actors,
        source=_text(value.get("source")) or "reviewer_runtime",
    )


def session_posture_actor_from_mapping(
    value: object,
) -> SessionPostureActor | None:
    """Deserialize one posture actor row."""
    if not isinstance(value, Mapping):
        return None
    actor_id = _text(value.get("actor_id"))
    provider = _text(value.get("provider")) or actor_id
    if not actor_id and not provider:
        return None
    return SessionPostureActor(
        actor_id=actor_id or provider,
        provider=provider,
        role=_text(value.get("role")),
        occupied_lane=normalize_occupied_lane(value.get("occupied_lane")),
        presence=_text(value.get("presence")),
        live=bool_value(value.get("live")),
        source=_text(value.get("source")),
        current_activity=normalize_current_activity(value.get("current_activity")),
        current_target=_text(value.get("current_target")),
        granted_capabilities=tuple(string_rows(value.get("granted_capabilities"))),
    )


def build_session_posture(
    *,
    interaction_mode: object = "",
    reviewer_mode: object = "",
    effective_reviewer_mode: object = "",
    collaboration: object | None = None,
    remote_control_attachment: object | None = None,
    agent_mind: object | None = None,
) -> SessionPosture:
    """Build posture without deriving lane occupancy from capability grants."""
    resolved_reviewer_mode = _text(reviewer_mode) or "single_agent"
    resolved_effective_mode = (
        _text(effective_reviewer_mode) or resolved_reviewer_mode
    )
    return SessionPosture(
        interaction_mode=resolve_interaction_mode(
            interaction_mode,
            remote_control_attachment=remote_control_attachment,
            effective_reviewer_mode=resolved_effective_mode,
        ),
        reviewer_mode=resolved_reviewer_mode,
        effective_reviewer_mode=resolved_effective_mode,
        actors=collect_session_posture_actors(
            actor_cls=SessionPostureActor,
            collaboration=collaboration,
            remote_control_attachment=remote_control_attachment,
            agent_mind=agent_mind,
        ),
    )


def normalize_occupied_lane(value: object) -> str:
    """Normalize a current occupied lane without treating grants as lanes."""
    return _normalize_occupied_lane(value)


def _text(value: object) -> str:
    return str(value or "").strip()
