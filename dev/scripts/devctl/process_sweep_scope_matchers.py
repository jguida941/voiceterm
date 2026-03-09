"""Scope-specific row matchers for process-sweep scans."""

from __future__ import annotations

import re
from typing import Any, Callable

from .process_sweep_config import (
    REPO_RUNTIME_CARGO_RE,
    REPO_RUNTIME_RELATIVE_TARGET_BINARY_RE,
    REPO_RUNTIME_TARGET_BINARY_RE,
    REPO_TOOLING_CWD_CANDIDATE_RE,
    REPO_TOOLING_WRAPPER_RE,
    VOICETERM_SWEEP_TARGET_RE,
)
from .process_sweep_core import (
    is_attached_noninteractive_repo_helper,
    is_repo_background_candidate,
    path_is_under_repo,
    row_looks_backgrounded,
    select_matching_rows,
)

RunCmd = Callable[..., Any]
LookupProcessCwds = Callable[..., tuple[dict[int, str], list[str]]]


def match_repo_cwd_candidate_pids(
    rows: list[dict],
    repo_cwd_candidate_regex: re.Pattern[str],
    *,
    run_cmd: RunCmd,
    lookup_process_cwds: LookupProcessCwds,
    candidate_filter: Callable[[dict], bool] | None = None,
) -> tuple[set[int], list[str]]:
    """Return candidate pids whose cwd resolves inside the current repo."""
    candidate_rows = [row for row in rows if repo_cwd_candidate_regex.search(row["command"])]
    if candidate_filter is not None:
        candidate_rows = [row for row in candidate_rows if candidate_filter(row)]
    cwd_map, cwd_warnings = lookup_process_cwds(candidate_rows, run_cmd=run_cmd)
    matched_pids = {
        row["pid"]
        for row in candidate_rows
        if path_is_under_repo(cwd_map.get(row["pid"]))
    }
    return matched_pids, cwd_warnings


def match_voiceterm_rows(rows: list[dict]) -> list[dict]:
    matched_pids = {
        row["pid"] for row in rows if VOICETERM_SWEEP_TARGET_RE.search(row["command"])
    }
    return select_matching_rows(rows, matched_pids, scope="voiceterm")


def match_repo_runtime_rows(
    rows: list[dict],
    *,
    run_cmd: RunCmd,
    lookup_process_cwds: LookupProcessCwds,
) -> tuple[list[dict], list[str]]:
    absolute_pids = {
        row["pid"] for row in rows if REPO_RUNTIME_TARGET_BINARY_RE.search(row["command"])
    }
    relative_cwd_pids, relative_warnings = match_repo_cwd_candidate_pids(
        rows,
        REPO_RUNTIME_RELATIVE_TARGET_BINARY_RE,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
    )
    cargo_cwd_pids, cargo_warnings = match_repo_cwd_candidate_pids(
        rows,
        REPO_RUNTIME_CARGO_RE,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
    )
    matched_pids = absolute_pids | relative_cwd_pids | cargo_cwd_pids
    return select_matching_rows(rows, matched_pids, scope="repo_runtime"), [
        *relative_warnings,
        *cargo_warnings,
    ]


def _tooling_candidate_filter(row: dict) -> bool:
    return (
        row.get("ppid") == 1
        or row_looks_backgrounded(row)
        or is_attached_noninteractive_repo_helper(row)
    )


def match_repo_tooling_rows(
    rows: list[dict],
    *,
    run_cmd: RunCmd,
    lookup_process_cwds: LookupProcessCwds,
) -> tuple[list[dict], list[str]]:
    tooling_cwd_pids, tooling_warnings = match_repo_cwd_candidate_pids(
        rows,
        REPO_TOOLING_WRAPPER_RE,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
    )
    generic_cwd_pids, generic_warnings = match_repo_cwd_candidate_pids(
        rows,
        REPO_TOOLING_CWD_CANDIDATE_RE,
        run_cmd=run_cmd,
        lookup_process_cwds=lookup_process_cwds,
        candidate_filter=_tooling_candidate_filter,
    )
    matched_pids = tooling_cwd_pids | generic_cwd_pids
    return select_matching_rows(rows, matched_pids, scope="repo_tooling"), [
        *tooling_warnings,
        *generic_warnings,
    ]


def match_repo_background_rows(
    rows: list[dict],
    *,
    run_cmd: RunCmd,
    lookup_process_cwds: LookupProcessCwds,
    cwd_map: dict[int, str] | None = None,
) -> tuple[list[dict], list[str]]:
    background_cwd_map = cwd_map
    cwd_warnings: list[str] = []
    if background_cwd_map is None:
        background_cwd_map, cwd_warnings = lookup_process_cwds(rows, run_cmd=run_cmd)
    enriched_rows = [
        {**row, "cwd": background_cwd_map.get(row["pid"], "")}
        for row in rows
    ]
    matched_pids = {
        row["pid"] for row in enriched_rows if is_repo_background_candidate(row)
    }
    return select_matching_rows(
        enriched_rows,
        matched_pids,
        scope="repo_background",
    ), cwd_warnings
