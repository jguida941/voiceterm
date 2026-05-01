"""Authority and capability readers for AgentLoopDecision."""

from __future__ import annotations

from collections.abc import Mapping

from .review_state_collaboration_models import (
    actor_authorities_from_value,
    granted_capabilities_for_actor as granted_capabilities_from_authorities,
)
from .value_coercion import coerce_bool, coerce_mapping as _mapping, coerce_text as _text

_MUTATION_CAPABILITIES = frozenset({"repo.stage", "repo.commit"})
_MUTATION_ACTIONS = frozenset({"implementation.edit", "vcs.stage", "vcs.commit"})


def authority_snapshot(
    *, review_state: Mapping[str, object], dashboard: Mapping[str, object],
) -> Mapping[str, object]:
    return (
        _mapping(review_state.get("authority_snapshot"))
        or _mapping(dashboard.get("authority_snapshot"))
        or _action_routing(review_state)
        or _action_routing(dashboard)
    )


def action_routing_decision(
    *, review_state: Mapping[str, object], dashboard: Mapping[str, object],
) -> Mapping[str, object]:
    return _action_routing(review_state) or _action_routing(dashboard)


def granted_capabilities_for_actor(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    actor: str,
    role: str = "",
    session: str = "",
) -> tuple[str, ...]:
    scoped_capabilities = scoped_work_board_capabilities(
        review_state=review_state,
        dashboard=dashboard,
        actor=actor,
        role=role,
        session=session,
    )
    if scoped_capabilities is not None:
        return scoped_capabilities

    capabilities: list[str] = []
    authority_capabilities = granted_capabilities_from_authorities(
        actor_authorities_from_value(authority_rows(review_state, dashboard)),
        actor,
    )
    capabilities.extend(authority_capabilities)
    rows = (*authority_rows(review_state, dashboard), *posture_actor_rows(review_state, dashboard))
    for row in rows:
        if not actor_row_matches(row, actor):
            continue
        values = string_tuple(row.get("granted_capabilities"))
        for capability in values:
            if capability not in capabilities:
                capabilities.append(capability)
    return tuple(capabilities)


def scoped_work_board_capabilities(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    actor: str,
    role: str = "",
    session: str = "",
) -> tuple[str, ...] | None:
    row = scoped_work_board_row(
        review_state=review_state,
        dashboard=dashboard,
        actor=actor,
        role=role,
        session=session,
    )
    if row is None:
        return None
    return string_tuple(row.get("granted_capabilities"))


def scoped_session_mutation_mode_allows(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    actor: str,
    role: str = "",
    session: str = "",
) -> bool:
    row = scoped_work_board_row(
        review_state=review_state,
        dashboard=dashboard,
        actor=actor,
        role=role,
        session=session,
    )
    if row is None:
        return True
    mutation_mode = _text(row.get("mutation_mode"))
    if not mutation_mode:
        return True
    return mutation_mode in {"live_tree", "isolated_worktree"}


def scoped_work_board_row(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    actor: str,
    role: str = "",
    session: str = "",
) -> Mapping[str, object] | None:
    actor_id = _text(actor).lower()
    role_id = _normalize_role(role)
    session_id = _text(session)
    if not actor_id:
        return None
    candidates = []
    for row in work_board_rows(review_state, dashboard):
        if not actor_row_matches(row, actor_id):
            continue
        if role_id and _normalize_role(row.get("role")) != role_id:
            continue
        if session_id and _text(row.get("session_id")) != session_id:
            continue
        candidates.append(row)
    if len(candidates) == 1:
        return candidates[0]
    return None


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


def actor_row_matches(row: Mapping[str, object], actor: str) -> bool:
    normalized = actor.lower()
    return normalized in {
        _text(row.get("actor_id")).lower(),
        _text(row.get("provider")).lower(),
        _text(row.get("agent_id")).lower(),
    }


def _normalize_role(value: object) -> str:
    text = _text(value).lower().replace("-", "_")
    if text in {"coder", "coding", "implementation"}:
        return "implementer"
    if text in {"review", "reviewer"}:
        return "reviewer"
    if text in {"observer", "watcher"}:
        return "dashboard"
    return text


def string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(_text(item) for item in value if _text(item))


def merged_actions(*sources: Mapping[str, object], key: str) -> tuple[str, ...]:
    actions: list[str] = []
    for source in sources:
        for action in string_tuple(source.get(key)):
            if action not in actions:
                actions.append(action)
    return tuple(actions)


def may_actor_mutate(
    *,
    granted_capabilities: tuple[str, ...],
    allowed_actions: tuple[str, ...],
    blocked_actions: tuple[str, ...],
    edit_allowed: bool,
) -> bool:
    if not edit_allowed:
        return False
    if not (_MUTATION_CAPABILITIES & set(granted_capabilities)):
        return False
    if _MUTATION_ACTIONS & set(blocked_actions):
        return False
    return not allowed_actions or bool(_MUTATION_ACTIONS & set(allowed_actions))


def lane_edit_allowed(
    *, review_state: Mapping[str, object], dashboard: Mapping[str, object],
) -> bool:
    gate = (
        _mapping(review_state.get("lane_edit_gate"))
        or _mapping(dashboard.get("lane_edit_gate"))
        or _mapping(_action_routing(review_state).get("agent_lane")).get("edit_gate")
        or _mapping(_action_routing(dashboard).get("agent_lane")).get("edit_gate")
    )
    gate_map = _mapping(gate)
    if not gate_map:
        return True
    return coerce_bool(gate_map.get("edit_allowed"))


def _action_routing(source: Mapping[str, object]) -> Mapping[str, object]:
    control_plane = _mapping(source.get("control_plane"))
    return _mapping(source.get("action_routing")) or _mapping(
        control_plane.get("action_routing")
    )


__all__ = [
    "action_routing_decision",
    "authority_snapshot",
    "granted_capabilities_for_actor",
    "lane_edit_allowed",
    "may_actor_mutate",
    "merged_actions",
    "scoped_session_mutation_mode_allows",
    "string_tuple",
]
