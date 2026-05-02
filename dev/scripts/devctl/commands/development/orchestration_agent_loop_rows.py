"""Agent-loop row sources for `/develop` orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ...review_channel.agent_loop_decision_projection import (
    agent_loop_decisions_for_work_board,
)


def agent_loop_rows(
    review_state: Mapping[str, object],
    *,
    dashboard: Mapping[str, object] | None = None,
) -> tuple[Mapping[str, object], ...]:
    """Return fresh agent-loop rows when runtime work-board state is available."""
    refreshed = _refreshed_agent_loop_rows(review_state, dashboard=dashboard)
    if refreshed:
        return refreshed
    rows = review_state.get("agent_loop_decisions")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _refreshed_agent_loop_rows(
    review_state: Mapping[str, object],
    *,
    dashboard: Mapping[str, object] | None = None,
) -> tuple[Mapping[str, object], ...]:
    work_board = review_state.get("agent_work_board")
    if not isinstance(work_board, Mapping):
        return ()
    rows = work_board.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        return ()
    decisions = agent_loop_decisions_for_work_board(
        review_state=review_state,
        work_board=work_board,
        dashboard=dashboard,
    )
    return tuple(row for row in decisions if isinstance(row, Mapping))


__all__ = ["agent_loop_rows"]
