"""Shared process-sweep facade used by `devctl check` and `devctl hygiene`."""

from __future__ import annotations

import os
import signal
import subprocess
import re

from .process_sweep_config import (
    DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    DEFAULT_STALE_MIN_AGE_SECONDS,
    PROCESS_CWD_LOOKUP_PREFIX,
    PROCESS_SWEEP_CMD,
    SECONDS_PER_DAY,
)
from .process_sweep_core import (
    build_skip_pid_set as _core_build_skip_pid_set,
    collect_descendant_rows as _collect_descendant_rows,
    command_executable_basename as _command_executable_basename,
    command_executable_token as _command_executable_token,
    expand_cleanup_target_rows,
    extend_process_row_markdown,
    format_process_rows,
    is_interactive_shell_command as _is_interactive_shell_command,
    is_repo_background_candidate as _is_repo_background_candidate,
    kill_processes as _core_kill_processes,
    merge_scanned_row_groups as _merge_scanned_row_groups,
    normalize_repo_path as _normalize_repo_path,
    parse_etime_seconds,
    path_is_under_repo,
    row_looks_backgrounded as _row_looks_backgrounded,
    render_process_row_markdown,
    select_matching_rows as _select_matching_rows,
    split_orphaned_processes,
    split_stale_processes,
)
from .process_sweep_scans import (
    lookup_process_cwds as _core_lookup_process_cwds,
    scan_matching_processes as _core_scan_matching_processes,
    scan_process_rows as _core_scan_process_rows,
    scan_repo_background_process_tree as _core_scan_repo_background_process_tree,
    scan_repo_hygiene_process_tree as _core_scan_repo_hygiene_process_tree,
    scan_repo_runtime_process_tree as _core_scan_repo_runtime_process_tree,
    scan_repo_tooling_process_tree as _core_scan_repo_tooling_process_tree,
    scan_voiceterm_test_process_tree as _core_scan_voiceterm_test_process_tree,
)


def _build_skip_pid_set(rows: list[dict], *, this_pid: int) -> set[int]:
    return _core_build_skip_pid_set(rows, this_pid=this_pid, parent_pid=os.getppid())


def _scan_process_rows(*, skip_pid: int | None = None) -> tuple[list[dict], list[str]]:
    return _core_scan_process_rows(
        skip_pid=skip_pid,
        run_cmd=subprocess.run,
        current_pid=os.getpid(),
        parent_pid=os.getppid(),
    )


def _lookup_process_cwds(rows: list[dict]) -> tuple[dict[int, str], list[str]]:
    return _core_lookup_process_cwds(rows, run_cmd=subprocess.run)


def scan_matching_processes(
    command_regex: re.Pattern[str],
    *,
    skip_pid: int | None = None,
    scope: str,
    repo_cwd_candidate_regex: re.Pattern[str] | None = None,
) -> tuple[list[dict], list[str]]:
    return _core_scan_matching_processes(
        command_regex,
        skip_pid=skip_pid,
        scope=scope,
        repo_cwd_candidate_regex=repo_cwd_candidate_regex,
        run_cmd=subprocess.run,
        current_pid=os.getpid(),
        parent_pid=os.getppid(),
    )


def scan_voiceterm_test_process_tree(
    *, skip_pid: int | None = None
) -> tuple[list[dict], list[str]]:
    return _core_scan_voiceterm_test_process_tree(
        skip_pid=skip_pid,
        run_cmd=subprocess.run,
        current_pid=os.getpid(),
        parent_pid=os.getppid(),
    )


def scan_repo_runtime_process_tree(
    *, skip_pid: int | None = None
) -> tuple[list[dict], list[str]]:
    return _core_scan_repo_runtime_process_tree(
        skip_pid=skip_pid,
        run_cmd=subprocess.run,
        current_pid=os.getpid(),
        parent_pid=os.getppid(),
    )


def scan_repo_tooling_process_tree(
    *, skip_pid: int | None = None
) -> tuple[list[dict], list[str]]:
    return _core_scan_repo_tooling_process_tree(
        skip_pid=skip_pid,
        run_cmd=subprocess.run,
        current_pid=os.getpid(),
        parent_pid=os.getppid(),
    )


def scan_repo_background_process_tree(
    *, skip_pid: int | None = None
) -> tuple[list[dict], list[str]]:
    return _core_scan_repo_background_process_tree(
        skip_pid=skip_pid,
        run_cmd=subprocess.run,
        current_pid=os.getpid(),
        parent_pid=os.getppid(),
    )


def scan_repo_hygiene_process_tree(
    *, skip_pid: int | None = None
) -> tuple[list[dict], list[str]]:
    return _core_scan_repo_hygiene_process_tree(
        skip_pid=skip_pid,
        run_cmd=subprocess.run,
        current_pid=os.getpid(),
        parent_pid=os.getppid(),
    )


def scan_voiceterm_test_binaries(
    *, skip_pid: int | None = None
) -> tuple[list[dict], list[str]]:
    return scan_voiceterm_test_process_tree(skip_pid=skip_pid)


def kill_processes(
    rows: list[dict], *, kill_signal: int = signal.SIGKILL
) -> tuple[list[int], list[str]]:
    return _core_kill_processes(rows, kill_fn=os.kill, kill_signal=kill_signal)
