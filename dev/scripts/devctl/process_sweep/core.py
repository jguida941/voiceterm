"""Shared process-sweep re-exports used by `devctl check` and `devctl hygiene`.

All runtime logic lives in the sub-modules (internals, scans, matching, config).
This module re-exports the public API so that existing callers keep working.
"""

from __future__ import annotations

from .config import (  # noqa: F401
    DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    DEFAULT_STALE_MIN_AGE_SECONDS,
    PROCESS_CWD_LOOKUP_PREFIX,
    PROCESS_SWEEP_CMD,
    SECONDS_PER_DAY,
)
from .internals import (  # noqa: F401
    expand_cleanup_target_rows,
    extend_process_row_markdown,
    format_process_rows,
    kill_processes,
    parse_etime_seconds,
    path_is_under_repo,
    render_process_row_markdown,
    split_orphaned_processes,
    split_stale_processes,
)
from .scans import (  # noqa: F401
    lookup_process_cwds,
    scan_matching_processes,
    scan_repo_background_process_tree,
    scan_repo_hygiene_process_tree,
    scan_repo_runtime_process_tree,
    scan_repo_tooling_process_tree,
    scan_voiceterm_test_process_tree,
    scan_voiceterm_test_process_tree as scan_voiceterm_test_binaries,
)
