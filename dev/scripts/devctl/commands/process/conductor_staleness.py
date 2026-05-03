"""Review-channel conductor staleness helpers for host process audits."""

from __future__ import annotations

import re

SUPERVISED_CONDUCTOR_SCOPE = "review_channel_conductor"

SESSION_HEAD_RE = re.compile(
    r'"head_sha"\s*:\s*"(?P<json>[0-9a-f]{40})"|'
    r"\bhead_sha[=:]\s*(?P<plain>[0-9a-f]{40})"
)


def _row_pid(row: dict) -> int:
    return int(row.get("pid", 0) or 0)


def _row_ppid(row: dict) -> int:
    return int(row.get("ppid", 0) or 0)


def _row_command(row: dict) -> str:
    return str(row.get("command") or row.get("cmd") or "")


def _row_session_head(row: dict) -> str:
    match = SESSION_HEAD_RE.search(_row_command(row))
    if not match:
        return ""
    return str(match.group("json") or match.group("plain") or "")


def _conductor_tree_rows(rows: list[dict], seed_rows: list[dict]) -> list[dict]:
    rows_by_pid = {_row_pid(row): row for row in rows if _row_pid(row) > 0}
    children_by_pid: dict[int, list[dict]] = {}
    for row in rows_by_pid.values():
        children_by_pid.setdefault(_row_ppid(row), []).append(row)

    root_pids: set[int] = set()
    for seed in seed_rows:
        current = seed
        root_pid = _row_pid(seed)
        while True:
            parent = rows_by_pid.get(_row_ppid(current))
            if parent is None:
                break
            if parent.get("match_scope") != SUPERVISED_CONDUCTOR_SCOPE:
                break
            root_pid = _row_pid(parent)
            current = parent
        root_pids.add(root_pid)

    selected: dict[int, dict] = {}
    stack = list(root_pids)
    while stack:
        pid = stack.pop()
        row = rows_by_pid.get(pid)
        if row is None or pid in selected:
            continue
        if row.get("match_scope") != SUPERVISED_CONDUCTOR_SCOPE:
            continue
        selected[pid] = row
        for child in children_by_pid.get(pid, []):
            if child.get("match_scope") == SUPERVISED_CONDUCTOR_SCOPE:
                stack.append(_row_pid(child))

    return sorted(
        selected.values(),
        key=lambda row: (row.get("lineage_depth", 0), row.get("elapsed_seconds", -1)),
        reverse=True,
    )


def stale_supervised_conductor_rows(
    rows: list[dict],
    supervised_rows: list[dict],
    *,
    current_head: str,
) -> list[dict]:
    """Return supervised conductor trees whose embedded resume head is stale."""
    if not current_head:
        return []

    stale_seed_rows = [
        row
        for row in supervised_rows
        if (session_head := _row_session_head(row)) and session_head != current_head
    ]
    return _conductor_tree_rows(rows, stale_seed_rows)
