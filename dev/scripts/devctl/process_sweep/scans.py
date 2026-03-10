"""Runtime helpers that interact with host process tools for process sweep."""

from __future__ import annotations

import os
import re
import subprocess
from typing import Any, Callable

from .config import (
    LSOF_PID_CHUNK_SIZE,
    PROCESS_CWD_LOOKUP_PREFIX,
    PROCESS_SWEEP_CMD,
    VOICETERM_SWEEP_TARGET_RE,
)
from .internals import (
    build_skip_pid_set,
    merge_scanned_row_groups,
    parse_etime_seconds,
    select_matching_rows,
)
from .scope_matchers import (
    match_review_channel_conductor_rows,
    match_repo_background_rows,
    match_repo_cwd_candidate_pids as _match_repo_cwd_candidate_pids,
    match_repo_runtime_rows,
    match_repo_tooling_rows,
    match_voiceterm_rows,
)


RunCmd = Callable[..., Any]


def scan_process_rows(
    *,
    skip_pid: int | None,
    run_cmd: RunCmd | None = None,
    current_pid: int | None = None,
    parent_pid: int | None = None,
) -> tuple[list[dict], list[str]]:
    """Read `ps` output into normalized process rows."""
    if run_cmd is None:
        run_cmd = subprocess.run
    if current_pid is None:
        current_pid = os.getpid()
    if parent_pid is None:
        parent_pid = os.getppid()
    warnings: list[str] = []
    try:
        result = run_cmd(
            PROCESS_SWEEP_CMD,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        warnings.append(f"Process sweep skipped: unable to execute ps ({exc})")
        return [], warnings

    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else "unknown ps error"
        warnings.append(
            f"Process sweep skipped: ps returned {result.returncode} ({stderr})"
        )
        return [], warnings

    rows: list[dict] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 4)
        if len(parts) != 5:
            continue
        pid_raw, ppid_raw, tty, etime, command = parts
        if not (pid_raw.isdigit() and ppid_raw.isdigit()):
            continue
        if "ps -axo pid=,ppid=,tty=,etime=,command=" in command:
            continue
        elapsed = parse_etime_seconds(etime)
        rows.append(
            {
                "pid": int(pid_raw),
                "ppid": int(ppid_raw),
                "tty": tty,
                "etime": etime,
                "elapsed_seconds": elapsed if elapsed is not None else -1,
                "command": command,
            }
        )

    resolved_skip_pid = current_pid if skip_pid is None else skip_pid
    skip_pids = build_skip_pid_set(rows, this_pid=resolved_skip_pid, parent_pid=parent_pid)
    return [row for row in rows if row["pid"] not in skip_pids], warnings


def lookup_process_cwds(rows: list[dict], *, run_cmd: RunCmd | None = None) -> tuple[dict[int, str], list[str]]:
    """Best-effort cwd lookup for a process snapshot using `lsof`."""
    if run_cmd is None:
        run_cmd = subprocess.run
    warnings: list[str] = []
    if not rows:
        return {}, warnings

    cwd_map: dict[int, str] = {}
    pid_values = [str(row["pid"]) for row in rows]
    for start in range(0, len(pid_values), LSOF_PID_CHUNK_SIZE):
        chunk = pid_values[start : start + LSOF_PID_CHUNK_SIZE]
        try:
            result = run_cmd(
                [*PROCESS_CWD_LOOKUP_PREFIX, ",".join(chunk)],
                check=False,
                capture_output=True,
                text=False,
            )
        except OSError as exc:
            warnings.append(f"cwd lookup skipped: unable to execute lsof ({exc})")
            return cwd_map, warnings

        if result.returncode not in {0, 1}:
            raw_stderr = result.stderr
            stderr = (
                raw_stderr.decode("utf-8", errors="replace").strip()
                if isinstance(raw_stderr, bytes)
                else str(raw_stderr or "").strip() or "unknown lsof error"
            )
            warnings.append(
                f"cwd lookup skipped: lsof returned {result.returncode} ({stderr})"
            )
            return cwd_map, warnings

        current_pid: int | None = None
        current_fd: str | None = None
        raw_stdout = result.stdout
        decoded = (
            raw_stdout.decode("utf-8", errors="replace")
            if isinstance(raw_stdout, bytes)
            else str(raw_stdout or "")
        )
        for token in decoded.split("\0"):
            if not token:
                continue
            cleaned = token.lstrip("\n")
            if not cleaned:
                continue
            tag = cleaned[0]
            value = cleaned[1:]
            if tag == "p":
                current_pid = int(value) if value.isdigit() else None
                current_fd = None
            elif tag == "f":
                current_fd = value
            elif tag == "n" and current_pid is not None and current_fd == "cwd":
                cwd_map[current_pid] = value
    return cwd_map, warnings


def match_repo_cwd_candidate_pids(
    rows: list[dict],
    repo_cwd_candidate_regex: re.Pattern[str],
    *,
    run_cmd: RunCmd,
    candidate_filter: Callable[[dict], bool] | None = None,
) -> tuple[set[int], list[str]]:
    return _match_repo_cwd_candidate_pids(
        rows,
        repo_cwd_candidate_regex,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
        candidate_filter=candidate_filter,
    )


def scan_matching_processes(
    command_regex: re.Pattern[str],
    *,
    skip_pid: int | None = None,
    scope: str,
    repo_cwd_candidate_regex: re.Pattern[str] | None = None,
    run_cmd: RunCmd | None = None,
    current_pid: int | None = None,
    parent_pid: int | None = None,
) -> tuple[list[dict], list[str]]:
    """Return rows whose command matches `command_regex` plus their descendants."""
    rows, warnings = scan_process_rows(
        skip_pid=skip_pid,
        run_cmd=run_cmd,
        current_pid=current_pid,
        parent_pid=parent_pid,
    )
    matched_pids = {row["pid"] for row in rows if command_regex.search(row["command"])}
    if repo_cwd_candidate_regex is not None:
        repo_cwd_pids, cwd_warnings = match_repo_cwd_candidate_pids(
            rows,
            repo_cwd_candidate_regex,
            run_cmd=run_cmd,
        )
        matched_pids.update(repo_cwd_pids)
        warnings.extend(cwd_warnings)
    return select_matching_rows(rows, matched_pids, scope=scope), warnings


def scan_voiceterm_test_process_tree(
    *,
    skip_pid: int | None = None,
    run_cmd: RunCmd | None = None,
    current_pid: int | None = None,
    parent_pid: int | None = None,
) -> tuple[list[dict], list[str]]:
    return scan_matching_processes(
        VOICETERM_SWEEP_TARGET_RE,
        skip_pid=skip_pid,
        scope="voiceterm",
        repo_cwd_candidate_regex=None,
        run_cmd=run_cmd,
        current_pid=current_pid,
        parent_pid=parent_pid,
    )


def scan_repo_runtime_process_tree(
    *,
    skip_pid: int | None = None,
    run_cmd: RunCmd | None = None,
    current_pid: int | None = None,
    parent_pid: int | None = None,
) -> tuple[list[dict], list[str]]:
    rows, warnings = scan_process_rows(
        skip_pid=skip_pid,
        run_cmd=run_cmd,
        current_pid=current_pid,
        parent_pid=parent_pid,
    )
    runtime_rows, runtime_warnings = match_repo_runtime_rows(
        rows,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
    )
    return runtime_rows, [*warnings, *runtime_warnings]


def scan_repo_tooling_process_tree(
    *,
    skip_pid: int | None = None,
    run_cmd: RunCmd | None = None,
    current_pid: int | None = None,
    parent_pid: int | None = None,
) -> tuple[list[dict], list[str]]:
    rows, warnings = scan_process_rows(
        skip_pid=skip_pid,
        run_cmd=run_cmd,
        current_pid=current_pid,
        parent_pid=parent_pid,
    )
    tooling_rows, tooling_warnings = match_repo_tooling_rows(
        rows,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
    )
    return tooling_rows, [*warnings, *tooling_warnings]


def scan_repo_background_process_tree(
    *,
    skip_pid: int | None = None,
    run_cmd: RunCmd | None = None,
    current_pid: int | None = None,
    parent_pid: int | None = None,
) -> tuple[list[dict], list[str]]:
    rows, warnings = scan_process_rows(
        skip_pid=skip_pid,
        run_cmd=run_cmd,
        current_pid=current_pid,
        parent_pid=parent_pid,
    )
    background_rows, background_warnings = match_repo_background_rows(
        rows,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
    )
    return background_rows, [*warnings, *background_warnings]


def scan_repo_hygiene_process_tree(
    *,
    skip_pid: int | None = None,
    run_cmd: RunCmd | None = None,
    current_pid: int | None = None,
    parent_pid: int | None = None,
) -> tuple[list[dict], list[str]]:
    rows, warnings = scan_process_rows(
        skip_pid=skip_pid,
        run_cmd=run_cmd,
        current_pid=current_pid,
        parent_pid=parent_pid,
    )
    cwd_map, cwd_warnings = lookup_process_cwds(rows, run_cmd=run_cmd)
    voiceterm_rows = match_voiceterm_rows(rows)
    conductor_rows = match_review_channel_conductor_rows(rows)
    runtime_rows, runtime_warnings = match_repo_runtime_rows(
        rows,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
    )
    tooling_rows, tooling_warnings = match_repo_tooling_rows(
        rows,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
    )
    background_rows, background_warnings = match_repo_background_rows(
        rows,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
        cwd_map=cwd_map,
    )
    merged_rows = merge_scanned_row_groups(
        voiceterm_rows,
        conductor_rows,
        runtime_rows,
        tooling_rows,
        background_rows,
    )
    return merged_rows, [
        *warnings,
        *cwd_warnings,
        *runtime_warnings,
        *tooling_warnings,
        *background_warnings,
    ]
