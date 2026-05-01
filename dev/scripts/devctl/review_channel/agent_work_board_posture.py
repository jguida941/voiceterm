"""Project work-board liveness into SessionPosture read models."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.session_posture_lanes import normalize_occupied_lane
from ..runtime.value_coercion import coerce_int


def apply_work_board_session_posture(
    review_state: Mapping[str, object],
) -> dict[str, object]:
    """Use fresh work-board rows to correct collaboration-only posture."""
    runtime = _mapping(review_state.get("reviewer_runtime"))
    posture = _mapping(runtime.get("session_posture"))
    actors = posture.get("actors")
    if not isinstance(actors, (list, tuple)):
        return dict(review_state)
    row_state = _work_board_state_by_actor(review_state)
    if not row_state:
        return dict(review_state)

    updated_actors: list[object] = []
    changed = False
    for actor in actors:
        if not isinstance(actor, Mapping):
            updated_actors.append(actor)
            continue
        actor_id = _text(actor.get("actor_id")) or _text(actor.get("provider"))
        state = row_state.get(actor_id)
        if state is None:
            updated_actors.append(actor)
            continue
        updated_actor = _apply_actor_state(actor, state)
        changed = changed or updated_actor != dict(actor)
        updated_actors.append(updated_actor)

    if not changed:
        return dict(review_state)
    updated_posture = dict(posture)
    updated_posture["actors"] = updated_actors
    updated_runtime = dict(runtime)
    updated_runtime["session_posture"] = updated_posture
    updated = dict(review_state)
    updated["reviewer_runtime"] = updated_runtime
    return updated


def _work_board_state_by_actor(
    review_state: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    board = _mapping(review_state.get("agent_work_board"))
    rows = board.get("rows")
    if not isinstance(rows, list):
        return {}
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        actor_id = _text(row.get("actor_id"))
        if actor_id:
            grouped.setdefault(actor_id, []).append(row)
    return {actor_id: _actor_state(rows) for actor_id, rows in grouped.items()}


def _actor_state(rows: list[Mapping[str, object]]) -> dict[str, object]:
    best = min(rows, key=lambda row: coerce_int(row.get("idle_seconds")))
    live = any(_row_is_live(row) for row in rows)
    return {
        "role": _text(best.get("role")),
        "occupied_lane": normalize_occupied_lane(best.get("role")),
        "live": live,
        "presence": "live" if live else "stale",
        "activity_age_seconds": coerce_int(best.get("idle_seconds")),
        "current_activity": _activity_for_row(best),
        "current_target": (
            _text(best.get("attention_packet_id"))
            or _text(best.get("active_packet_id"))
            or _text(best.get("lane_id"))
        ),
        "granted_capabilities": _string_rows(best.get("granted_capabilities")),
        "source": "agent_work_board",
    }


def _apply_actor_state(
    actor: Mapping[str, object],
    state: Mapping[str, object],
) -> dict[str, object]:
    updated = dict(actor)
    updated["live"] = bool(state.get("live"))
    role = _text(state.get("role"))
    if role:
        updated["role"] = role
        updated["occupied_lane"] = (
            _text(state.get("occupied_lane")) or _text(actor.get("occupied_lane"))
        )
    updated["presence"] = _text(state.get("presence"))
    updated["activity_age_seconds"] = coerce_int(state.get("activity_age_seconds"))
    updated["current_activity"] = _text(state.get("current_activity")) or "waiting"
    updated["current_target"] = _text(state.get("current_target"))
    updated["granted_capabilities"] = list(_string_rows(state.get("granted_capabilities")))
    updated["source"] = _text(state.get("source")) or _text(actor.get("source"))
    return updated


def _row_is_live(row: Mapping[str, object]) -> bool:
    if _text(row.get("confidence_class")) == "stale":
        return False
    stale_after = coerce_int(row.get("stale_after_seconds"))
    idle = coerce_int(row.get("idle_seconds"))
    if stale_after and idle > stale_after:
        return False
    return _text(row.get("status")) in {"working", "blocked", "polling", "checkpointed"}


def _activity_for_row(row: Mapping[str, object]) -> str:
    status = _text(row.get("status"))
    role = _text(row.get("role"))
    if status == "polling":
        return "running_guards"
    if status == "working" and role == "implementer":
        return "writing_code"
    if status in {"working", "blocked", "checkpointed"}:
        return "reading"
    return "waiting"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _string_rows(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(_text(item) for item in value if _text(item))


def _text(value: object) -> str:
    return str(value or "").strip()
