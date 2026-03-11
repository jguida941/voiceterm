"""Pure helpers for repo process matching and formatting."""

from __future__ import annotations

import os
from collections import defaultdict, deque
from pathlib import Path
import signal

from .config import (
    DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    DEFAULT_STALE_MIN_AGE_SECONDS,
    REPO_ROOT_RESOLVED,
    SCOPE_PRIORITY,
    SECONDS_PER_DAY,
    SELF_HYGIENE_COMMAND_RE,
)
from .matching import (
    command_executable_basename,
    command_executable_token,
    is_attached_noninteractive_repo_helper,
    is_interactive_shell_command,
    is_repo_background_candidate,
    normalize_repo_path,
    path_is_under_repo,
    row_looks_backgrounded,
)


def parse_etime_seconds(raw: str) -> int | None:
    """Convert `ps etime` text into seconds so age checks are easy."""
    trimmed = raw.strip()
    if not trimmed:
        return None

    days = 0
    rest = trimmed
    if "-" in trimmed:
        day_part, rest = trimmed.split("-", 1)
        if not day_part.isdigit():
            return None
        days = int(day_part)

    chunks = rest.split(":")
    if len(chunks) == 2:
        mm, ss = chunks
        if not (mm.isdigit() and ss.isdigit()):
            return None
        seconds = int(mm) * 60 + int(ss)
    elif len(chunks) == 3:
        hh, mm, ss = chunks
        if not (hh.isdigit() and mm.isdigit() and ss.isdigit()):
            return None
        seconds = int(hh) * 3600 + int(mm) * 60 + int(ss)
    else:
        return None

    return days * SECONDS_PER_DAY + seconds


def _build_process_tree_indexes(
    rows: list[dict],
) -> tuple[dict[int, dict], dict[int, list[int]]]:
    rows_by_pid = {row["pid"]: row for row in rows}
    children_by_pid: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        children_by_pid[row["ppid"]].append(row["pid"])
    return rows_by_pid, children_by_pid


def _walk_process_tree(children_by_pid: dict[int, list[int]], root_pids: list[int]) -> list[int]:
    ordered_pids: list[int] = []
    seen: set[int] = set()
    queue: deque[int] = deque(root_pids)
    while queue:
        pid = queue.popleft()
        if pid in seen:
            continue
        seen.add(pid)
        ordered_pids.append(pid)
        queue.extend(children_by_pid.get(pid, []))
    return ordered_pids


def _assign_lineage_depths(selected: dict[int, dict]) -> None:
    selected_pids = set(selected)
    for row in selected.values():
        depth = 0
        current_ppid = row["ppid"]
        while current_ppid in selected_pids:
            depth += 1
            current_ppid = selected[current_ppid]["ppid"]
        row["lineage_depth"] = depth


def build_skip_pid_set(rows: list[dict], *, this_pid: int, parent_pid: int) -> set[int]:
    """Return the current process subtree plus its ancestor chain."""
    rows_by_pid, children_by_pid = _build_process_tree_indexes(rows)

    skip_pids = {this_pid}
    next_pid = parent_pid
    while next_pid > 0 and next_pid not in skip_pids:
        skip_pids.add(next_pid)
        parent_row = rows_by_pid.get(next_pid)
        if parent_row is None:
            break
        next_pid = parent_row["ppid"]

    sibling_roots: list[int] = []
    for row in rows:
        if row["ppid"] != parent_pid:
            continue
        if SELF_HYGIENE_COMMAND_RE.search(row["command"]):
            sibling_roots.append(row["pid"])

    for pid in sibling_roots:
        skip_pids.add(pid)
        for child_pid in _walk_process_tree(children_by_pid, children_by_pid.get(pid, [])):
            skip_pids.add(child_pid)

    for pid in _walk_process_tree(children_by_pid, children_by_pid.get(this_pid, [])):
        skip_pids.add(pid)
    return skip_pids


def collect_descendant_rows(
    rows: list[dict], matched_pids: set[int], *, scope: str
) -> dict[int, dict]:
    """Return directly matched rows plus their descendant process tree."""
    rows_by_pid, children_by_pid = _build_process_tree_indexes(rows)

    selected: dict[int, dict] = {}
    for pid in _walk_process_tree(children_by_pid, list(matched_pids)):
        row = rows_by_pid.get(pid)
        if row is None or pid in selected:
            continue
        annotated = dict(row)
        annotated["match_source"] = "direct" if pid in matched_pids else "descendant"
        annotated["match_scope"] = scope
        selected[pid] = annotated
    _assign_lineage_depths(selected)
    return selected


def select_matching_rows(rows: list[dict], matched_pids: set[int], *, scope: str) -> list[dict]:
    if not matched_pids:
        return []
    expanded_rows = list(collect_descendant_rows(rows, matched_pids, scope=scope).values())
    expanded_rows.sort(
        key=lambda row: (row["elapsed_seconds"], row.get("lineage_depth", 0)),
        reverse=True,
    )
    return expanded_rows


def merge_scanned_row_groups(*row_groups: list[dict]) -> list[dict]:
    """Merge multiple scanned process groups without duplicating shared pids."""

    def row_priority(row: dict) -> tuple[int, int]:
        return (
            SCOPE_PRIORITY.get(str(row.get("match_scope", "")), 0),
            1 if row.get("match_source") == "direct" else 0,
        )

    merged: dict[int, dict] = {}
    for group in row_groups:
        for row in group:
            pid = row["pid"]
            existing = merged.get(pid)
            if existing is None or row_priority(row) > row_priority(existing):
                merged[pid] = row
    merged_rows = list(merged.values())
    merged_rows.sort(
        key=lambda row: (row["elapsed_seconds"], row.get("lineage_depth", 0)),
        reverse=True,
    )
    return merged_rows


def split_orphaned_processes(
    rows: list[dict], *, min_age_seconds: int = DEFAULT_ORPHAN_MIN_AGE_SECONDS
) -> tuple[list[dict], list[dict]]:
    """Split rows into `orphaned` vs `active` using PPID=1 + minimum age."""
    orphaned = [
        row
        for row in rows
        if row["ppid"] == 1 and row["elapsed_seconds"] >= min_age_seconds
    ]
    active = [row for row in rows if row not in orphaned]
    return orphaned, active


def split_stale_processes(
    rows: list[dict], *, min_age_seconds: int = DEFAULT_STALE_MIN_AGE_SECONDS
) -> tuple[list[dict], list[dict]]:
    """Split rows into `stale` vs `recent` using elapsed runtime age."""
    stale = [
        row
        for row in rows
        if row["elapsed_seconds"] >= 0 and row["elapsed_seconds"] >= min_age_seconds
    ]
    recent = [row for row in rows if row not in stale]
    return stale, recent


def expand_cleanup_target_rows(rows: list[dict], cleanup_root_rows: list[dict]) -> list[dict]:
    """Expand cleanup roots to their full descendant tree."""
    if not cleanup_root_rows:
        return []

    rows_by_pid, children_by_pid = _build_process_tree_indexes(rows)

    selected: dict[int, dict] = {}
    cleanup_root_pids = [row["pid"] for row in cleanup_root_rows]
    for pid in _walk_process_tree(children_by_pid, cleanup_root_pids):
        row = rows_by_pid.get(pid)
        if row is None or pid in selected:
            continue
        selected[pid] = row

    expanded_rows = list(selected.values())
    expanded_rows.sort(
        key=lambda row: (row.get("lineage_depth", 0), row.get("elapsed_seconds", -1)),
        reverse=True,
    )
    return expanded_rows


def kill_processes(
    rows: list[dict],
    *,
    kill_fn=None,
    kill_signal: int = signal.SIGKILL,
) -> tuple[list[int], list[str]]:
    """Best-effort kill for rows we already decided are safe to stop."""
    if kill_fn is None:
        kill_fn = os.kill
    killed_pids: list[int] = []
    warnings: list[str] = []
    rows_by_pid = {row["pid"]: row for row in rows}
    ordered_rows = sorted(
        rows_by_pid.values(),
        key=lambda row: (row.get("lineage_depth", 0), row["elapsed_seconds"]),
        reverse=True,
    )
    for row in ordered_rows:
        pid = row["pid"]
        try:
            kill_fn(pid, kill_signal)
            killed_pids.append(pid)
        except ProcessLookupError:
            continue
        except PermissionError as exc:
            warnings.append(f"pid={pid} permission denied ({exc})")
        except OSError as exc:
            warnings.append(f"pid={pid} kill failed ({exc})")
    return killed_pids, warnings


def render_process_row_markdown(row: dict) -> str:
    cwd = f" cwd={row['cwd']}" if row.get("cwd") else ""
    return (
        "- "
        f"pid={row['pid']} ppid={row['ppid']} etime={row['etime']} "
        f"scope={row.get('match_scope', 'unknown')} "
        f"source={row.get('match_source', 'direct')} cmd={row['command']}"
        f"{cwd}"
    )


def extend_process_row_markdown(
    lines: list[str],
    rows: list[dict],
    *,
    row_limit: int,
    overflow_label: str,
) -> None:
    for row in rows[:row_limit]:
        lines.append(render_process_row_markdown(row))
    remaining = len(rows) - min(len(rows), row_limit)
    if remaining > 0:
        lines.append(f"- ... {remaining} more {overflow_label}")


def format_process_rows(
    rows: list[dict], *, line_max_len: int = 180, row_limit: int = 8
) -> str:
    """Render short process summaries for human-readable warnings/errors."""

    def truncate(command: str) -> str:
        return command if len(command) <= line_max_len else command[: line_max_len - 3] + "..."

    def render_source(row: dict) -> str:
        parts: list[str] = []
        scope = row.get("match_scope")
        source = row.get("match_source")
        cwd = row.get("cwd")
        if scope:
            parts.append(f"scope={scope}")
        if source:
            parts.append(f"source={source}")
        if cwd:
            normalized = normalize_repo_path(cwd)
            display_cwd = cwd
            if normalized is not None:
                try:
                    relative = normalized.relative_to(REPO_ROOT_RESOLVED)
                    display_cwd = "." if relative == Path(".") else relative.as_posix()
                except ValueError:
                    pass
            parts.append(f"cwd={display_cwd}")
        return "" if not parts else " " + " ".join(parts)

    return "; ".join(
        f"pid={row['pid']} ppid={row['ppid']} etime={row['etime']}"
        f"{render_source(row)} cmd={truncate(row['command'])}"
        for row in rows[:row_limit]
    )
