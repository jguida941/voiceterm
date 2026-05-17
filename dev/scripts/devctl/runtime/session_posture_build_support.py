"""Build helpers for SessionPosture actor occupancy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .agent_mind_projection_read import agent_mind_latest_age_seconds
from .session_posture_interaction import (
    remote_attachment_active,
    resolve_interaction_mode,
)
from .session_posture_lanes import normalize_occupied_lane
from .session_posture_merge import merge_actor

_ACTIVITIES = frozenset(
    {
        "reading",
        "designing",
        "writing_code",
        "writing_tests",
        "running_tests",
        "running_guards",
        "committing",
        "pushing",
        "waiting",
    }
)


def collect_session_posture_actors(
    *,
    actor_cls,
    collaboration: object | None,
    remote_control_attachment: object | None,
    agent_mind: object | None,
) -> tuple[object, ...]:
    """Collect actor rows without deriving occupancy from capability grants."""
    actors: dict[str, object] = {}
    if remote_attachment_active(remote_control_attachment):
        merge_actor(
            actors,
            actor_cls(
                actor_id=_provider(remote_control_attachment) or "operator",
                provider=_provider(remote_control_attachment) or "operator",
                role=_role(remote_control_attachment) or "operator",
                occupied_lane="dashboard",
                presence="live",
                live=True,
                source="remote_control_attachment",
                current_activity="waiting",
                current_target=_remote_target(remote_control_attachment),
            ),
        )
    for participant in tuple(getattr(collaboration, "participants", ()) or ()):
        merge_actor(actors, _participant_actor(actor_cls, participant))
    for actor in _owner_actors(actor_cls, collaboration):
        merge_actor(actors, actor)
    for authority in tuple(getattr(collaboration, "actor_authorities", ()) or ()):
        merge_actor(actors, _authority_actor(actor_cls, authority))
    merge_actor(actors, _agent_mind_actor(actor_cls, agent_mind))
    return tuple(actors.values())


def _participant_actor(actor_cls, participant: object) -> object | None:
    actor_id = _text(getattr(participant, "agent_id", "")) or _text(
        getattr(participant, "provider", "")
    )
    if not actor_id:
        return None
    role = _text(getattr(participant, "role", ""))
    return actor_cls(
        actor_id=actor_id,
        provider=_text(getattr(participant, "provider", "")) or actor_id,
        role=role,
        occupied_lane=normalize_occupied_lane(role),
        presence="live" if bool(getattr(participant, "live", False)) else "configured",
        live=bool(getattr(participant, "live", False)),
        source="collaboration_participant",
        current_activity=_activity_for_lane(role),
        current_target=_text(getattr(participant, "summary", "")),
    )


def _owner_actors(actor_cls, collaboration: object | None) -> tuple[object, ...]:
    if collaboration is None:
        return ()
    rows = []
    for field_name, lane in (
        ("watcher_owner", "dashboard"),
        ("verification_owner", "reviewer"),
        ("mutation_owner", "implementer"),
    ):
        actor_id = _text(getattr(collaboration, field_name, ""))
        if actor_id:
            rows.append(
                actor_cls(
                    actor_id=actor_id,
                    provider=actor_id,
                    occupied_lane=lane,
                    source=field_name,
                    current_activity=_activity_for_lane(lane),
                    current_target=field_name,
                )
            )
    return tuple(rows)


def _authority_actor(actor_cls, authority: object) -> object | None:
    actor_id = _text(getattr(authority, "actor_id", ""))
    if not actor_id:
        return None
    return actor_cls(
        actor_id=actor_id,
        provider=_text(getattr(authority, "provider", "")) or actor_id,
        role=_text(getattr(authority, "role", "")),
        presence=_text(getattr(authority, "status", "")),
        live=bool(getattr(authority, "live", False)),
        source=_text(getattr(authority, "source", "")) or "actor_authority",
        current_activity=_activity_for_lane(_text(getattr(authority, "role", ""))),
        current_target=_text(getattr(authority, "target_ref", "")),
        granted_capabilities=tuple(
            _text(getattr(grant, "capability", ""))
            for grant in tuple(getattr(authority, "grants", ()) or ())
            if bool(getattr(grant, "granted", False))
            and _text(getattr(grant, "capability", ""))
        ),
    )


def _agent_mind_actor(actor_cls, agent_mind: object | None) -> object | None:
    if not isinstance(agent_mind, Mapping) or not agent_mind:
        return None
    provider = _text(agent_mind.get("agent_provider")) or "codex"
    age_seconds = agent_mind_latest_age_seconds(agent_mind)
    if age_seconds is None:
        return None
    live = age_seconds <= 300
    return actor_cls(
        actor_id=provider,
        provider=provider,
        presence="live" if live else "stale",
        live=live,
        source="agent_mind",
        activity_age_seconds=int(age_seconds),
        current_activity=_agent_mind_activity(agent_mind),
        current_target=_agent_mind_target(agent_mind),
    )


def _provider(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return _text(value.get("provider"))
    return _text(getattr(value, "provider", ""))


def _role(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return _text(value.get("role"))
    return _text(getattr(value, "role", ""))


def string_rows(value: object) -> list[str]:
    """Return non-blank string rows from a JSON sequence."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [_text(item) for item in value if _text(item)]


def bool_value(value: object) -> bool:
    """Coerce common JSON truthy values to bool."""
    if isinstance(value, bool):
        return value
    return _text(value).lower() in {"1", "true", "yes", "live", "attached"}


def _text(value: object) -> str:
    return str(value or "").strip()


def normalize_current_activity(value: object) -> str:
    """Normalize operator-facing activity labels to the closed enum."""
    text = _text(value).lower().replace("-", "_")
    return text if text in _ACTIVITIES else "waiting"


def _activity_for_lane(value: object) -> str:
    lane = normalize_occupied_lane(value)
    if lane == "implementer":
        return "writing_code"
    if lane == "reviewer":
        return "reading"
    if lane == "dashboard":
        return "waiting"
    return "waiting"


def _remote_target(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return _text(value.get("remote_session_id")) or _text(value.get("session_name"))
    return _text(getattr(value, "remote_session_id", "")) or _text(
        getattr(value, "session_name", "")
    )


def _agent_mind_activity(agent_mind: Mapping[str, object]) -> str:
    events = agent_mind.get("events")
    latest = events[-1] if isinstance(events, list) and events else {}
    event_type = _text(latest.get("event_type") if isinstance(latest, Mapping) else "")
    tool_name = _text(latest.get("tool_name") if isinstance(latest, Mapping) else "")
    haystack = f"{event_type} {tool_name}".lower()
    if "test" in haystack:
        return "running_tests"
    if "guard" in haystack or "check" in haystack:
        return "running_guards"
    if "write" in haystack or "edit" in haystack or "patch" in haystack:
        return "writing_code"
    return "reading" if haystack.strip() else "waiting"


def _agent_mind_target(agent_mind: Mapping[str, object]) -> str:
    events = agent_mind.get("events")
    latest = events[-1] if isinstance(events, list) and events else {}
    if not isinstance(latest, Mapping):
        return ""
    return _text(latest.get("summary")) or _text(latest.get("tool_name"))


__all__ = [
    "bool_value",
    "collect_session_posture_actors",
    "normalize_current_activity",
    "normalize_occupied_lane",
    "remote_attachment_active",
    "resolve_interaction_mode",
    "string_rows",
]
