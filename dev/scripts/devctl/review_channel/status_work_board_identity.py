"""Refresh preserved work-board rows from live collaboration identity."""

from __future__ import annotations

from collections.abc import Mapping


def refresh_preserved_work_board_runtime_identity(
    work_board: object,
    *,
    collaboration: object,
) -> object:
    """Keep event-owned rows but refresh workspace identity from live session state."""
    if not isinstance(work_board, Mapping):
        return work_board
    rows = work_board.get("rows")
    if not isinstance(rows, list):
        return work_board
    participants = _participants_by_actor_and_role(collaboration)
    if not participants:
        return work_board
    updated_rows: list[object] = []
    changed = False
    for row in rows:
        updated, row_changed = _refreshed_work_row(row, participants)
        changed = changed or row_changed
        updated_rows.append(updated)
    if not changed:
        return work_board
    refreshed = dict(work_board)
    refreshed["rows"] = updated_rows
    return refreshed


def _refreshed_work_row(
    row: object,
    participants: dict[tuple[str, str], Mapping[str, object]],
) -> tuple[object, bool]:
    if not isinstance(row, Mapping):
        return row, False
    participant = _participant_for_work_row(participants, row)
    if participant is None:
        return row, False
    updated = dict(row)
    workspace_root = _text(participant.get("workspace_root"))
    worktree = _text(participant.get("worktree")) or workspace_root
    branch = _text(participant.get("branch"))
    if worktree and not _text(updated.get("worktree_identity")):
        updated["worktree_identity"] = worktree
    if branch and not _text(updated.get("branch")):
        updated["branch"] = branch
    path_scope = updated.get("path_scope")
    if workspace_root and not (
        isinstance(path_scope, list) and any(_text(item) for item in path_scope)
    ):
        updated["path_scope"] = [workspace_root]
    return updated, updated != dict(row)


def _participants_by_actor_and_role(
    collaboration: object,
) -> dict[tuple[str, str], Mapping[str, object]]:
    if not isinstance(collaboration, Mapping):
        return {}
    rows = collaboration.get("participants")
    if not isinstance(rows, (list, tuple)):
        return {}
    indexed: dict[tuple[str, str], Mapping[str, object]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        actor = _text(row.get("agent_id")) or _text(row.get("provider"))
        role = _text(row.get("role"))
        if not actor:
            continue
        if role:
            indexed[(actor, role)] = row
        indexed.setdefault((actor, ""), row)
    return indexed


def _participant_for_work_row(
    participants: dict[tuple[str, str], Mapping[str, object]],
    row: Mapping[str, object],
) -> Mapping[str, object] | None:
    actor = _text(row.get("actor_id")) or _text(row.get("provider"))
    role = _text(row.get("role"))
    if not actor:
        return None
    return participants.get((actor, role)) or participants.get((actor, ""))


def _text(value: object) -> str:
    return str(value or "").strip()
