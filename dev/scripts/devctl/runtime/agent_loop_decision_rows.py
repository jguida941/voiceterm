"""Row readers for AgentLoopDecision authority inputs."""

from __future__ import annotations

from collections.abc import Mapping

from .value_coercion import coerce_mapping as _mapping, coerce_text as _text


def work_board_rows(
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    for source in (
        _mapping(review_state.get("agent_work_board")),
        _mapping(review_state.get("work_board")),
        _mapping(dashboard.get("agent_work_board")),
        _mapping(dashboard.get("work_board")),
    ):
        raw_rows = source.get("rows")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, Mapping))
    return tuple(rows)


def authority_rows(
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    for source in (
        _mapping(review_state.get("authority_snapshot")),
        _mapping(review_state.get("collaboration")),
        _mapping(dashboard.get("authority_snapshot")),
    ):
        raw_rows = source.get("actor_authorities")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, Mapping))
    return tuple(rows)


def posture_actor_rows(
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    reviewer_runtime = _mapping(review_state.get("reviewer_runtime"))
    control_plane = _mapping(dashboard.get("control_plane"))
    for posture in (
        _mapping(dashboard.get("session_posture")),
        _mapping(control_plane.get("session_posture")),
        _mapping(reviewer_runtime.get("session_posture")),
    ):
        raw_rows = posture.get("actors")
        if isinstance(raw_rows, list):
            return tuple(row for row in raw_rows if isinstance(row, Mapping))
    return ()


def participant_rows(
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    for source in (
        _mapping(review_state.get("collaboration")),
        _mapping(_mapping(review_state.get("reviewer_runtime")).get("collaboration")),
        _mapping(dashboard.get("collaboration")),
        _mapping(_mapping(dashboard.get("reviewer_runtime")).get("collaboration")),
    ):
        raw_rows = source.get("participants")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, Mapping))
    return tuple(rows)


def actor_row_matches(row: Mapping[str, object], actor: str) -> bool:
    normalized = actor.lower()
    return normalized in {
        _text(row.get("actor_id")).lower(),
        _text(row.get("provider")).lower(),
        _text(row.get("agent_id")).lower(),
    }


def row_role_matches_requested_role(
    row: Mapping[str, object],
    *,
    role: str = "",
    require_explicit_role: bool = False,
) -> bool:
    requested = normalize_role(role)
    if not requested:
        return True
    row_role = normalize_role(row.get("role"))
    if not row_role:
        return not require_explicit_role
    return row_role == requested


def normalize_role(value: object) -> str:
    text = _text(value).lower().replace("-", "_")
    if text in {"coder", "coding", "implementation"}:
        return "implementer"
    if text in {"review", "reviewer"}:
        return "reviewer"
    if text in {"observer", "watcher"}:
        return "dashboard"
    return text


__all__ = [
    "actor_row_matches",
    "authority_rows",
    "normalize_role",
    "participant_rows",
    "posture_actor_rows",
    "row_role_matches_requested_role",
    "work_board_rows",
]
