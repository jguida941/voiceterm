"""Shared runtime row readers for `/develop` collaboration projections."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def work_board_rows(
    review_state: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    """Return typed agent work-board rows from a review-state projection."""
    work_board = mapping(review_state.get("agent_work_board"))
    rows = work_board.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def text(value: object) -> str:
    return str(value or "").strip()


def int_or_none(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = ["int_or_none", "mapping", "text", "work_board_rows"]
