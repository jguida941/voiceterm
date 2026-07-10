"""Scoped work-board grants for agent-loop decisions."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_loop_decision_rows import (
    actor_row_matches,
    normalize_role,
    work_board_rows,
)
from .agent_loop_decision_values import string_tuple
from .value_coercion import coerce_text as _text


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
    role_id = normalize_role(role)
    session_id = _text(session)
    if not actor_id:
        return None
    candidates = []
    for row in work_board_rows(review_state, dashboard):
        if not actor_row_matches(row, actor_id):
            continue
        if role_id and normalize_role(row.get("role")) != role_id:
            continue
        if session_id and _text(row.get("session_id")) != session_id:
            continue
        candidates.append(row)
    if len(candidates) == 1:
        return candidates[0]
    return None


__all__ = [
    "scoped_session_mutation_mode_allows",
    "scoped_work_board_capabilities",
    "scoped_work_board_row",
]
