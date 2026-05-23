"""Refresh preserved work-board rows from live collaboration identity."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_work_board_roles import build_runtime_role_index


def refresh_preserved_work_board_runtime_identity(
    work_board: object,
    *,
    collaboration: object,
) -> object:
    """Keep event-owned rows but refresh identity from typed collaboration state."""
    if not isinstance(work_board, Mapping):
        return work_board
    rows = work_board.get("rows")
    if not isinstance(rows, list):
        return work_board
    participants = _participants_by_actor_and_role(collaboration)
    if not participants and not isinstance(collaboration, Mapping):
        return work_board
    role_index = build_runtime_role_index(
        collaboration if isinstance(collaboration, Mapping) else {}
    )
    updated_rows: list[object] = []
    changed = False
    for row in rows:
        updated, row_changed = _refreshed_work_row(row, participants, role_index)
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
    role_index: object,
) -> tuple[object, bool]:
    if not isinstance(row, Mapping):
        return row, False
    participant = _participant_for_work_row(participants, row)
    if participant is None:
        return row, False
    updated = dict(row)
    _refresh_role_identity(updated, participant, role_index)
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


def _refresh_role_identity(
    row: dict[str, object],
    participant: Mapping[str, object],
    role_index: object,
) -> None:
    """Refresh stale preserved rows without reauthorizing helper sidecars."""
    if _text(row.get("role_source")) == "helper_session_demotion":
        return
    actor = _text(row.get("actor_id")) or _text(row.get("provider"))
    if not actor:
        return
    provider = _text(row.get("provider")) or _text(participant.get("provider")) or actor
    declared_role = (
        _text(participant.get("role"))
        or _text(row.get("declared_role"))
        or _text(row.get("role"))
    )
    resolution = role_index.resolve(
        actor_id=actor,
        provider=provider,
        declared_role=declared_role,
    )
    if not resolution.role:
        return
    row["role"] = resolution.role
    row["declared_role"] = resolution.declared_role
    row["authority_role"] = resolution.authority_role
    row["role_source"] = resolution.role_source
    row["role_scope"] = resolution.role_scope
    row["mutation_mode"] = resolution.mutation_mode
    row["granted_capabilities"] = list(resolution.granted_capabilities)


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
