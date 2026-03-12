"""Shared process-sweep re-exports used by `devctl check` and `devctl hygiene`.

All runtime logic lives in the sub-modules (internals, scans, matching, config).
This module re-exports the public API so that existing callers keep working.
"""

from __future__ import annotations

from .config import (
    DEFAULT_ORPHAN_MIN_AGE_SECONDS as DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    DEFAULT_STALE_MIN_AGE_SECONDS as DEFAULT_STALE_MIN_AGE_SECONDS,
    PROCESS_CWD_LOOKUP_PREFIX as PROCESS_CWD_LOOKUP_PREFIX,
    PROCESS_SWEEP_CMD as PROCESS_SWEEP_CMD,
    SECONDS_PER_DAY as SECONDS_PER_DAY,
)
from .internals import (
    expand_cleanup_target_rows as expand_cleanup_target_rows,
    extend_process_row_markdown as extend_process_row_markdown,
    format_process_rows as format_process_rows,
    kill_processes as kill_processes,
    parse_etime_seconds as parse_etime_seconds,
    render_process_row_markdown as render_process_row_markdown,
    split_orphaned_processes as split_orphaned_processes,
    split_stale_processes as split_stale_processes,
)
from .matching import path_is_under_repo as path_is_under_repo
from .scans import (
    lookup_process_cwds as lookup_process_cwds,
    scan_matching_processes as scan_matching_processes,
    scan_repo_background_process_tree as scan_repo_background_process_tree,
    scan_repo_hygiene_process_tree as scan_repo_hygiene_process_tree,
    scan_repo_runtime_process_tree as scan_repo_runtime_process_tree,
    scan_repo_tooling_process_tree as scan_repo_tooling_process_tree,
    scan_voiceterm_test_process_tree as scan_voiceterm_test_process_tree,
    scan_voiceterm_test_process_tree as scan_voiceterm_test_binaries,
)
