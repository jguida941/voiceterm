"""Shared command-runner helpers plus compatibility re-exports for devctl."""

from pathlib import Path
import subprocess

from .command_runner import (
    CommandRunPolicy,
    CommandRunResult,
    FAILURE_OUTPUT_MAX_CHARS,
    FAILURE_OUTPUT_MAX_LINES,
    INTERRUPT_KILL_GRACE_SECONDS,
    LIVE_OUTPUT_TIMEOUT_SECONDS,
    POST_EXIT_STDOUT_DRAIN_SECONDS,
    _enqueue_stdout_lines,
    _resolve_live_output_timeout_seconds,
    _run_with_live_output,
    _run_without_live_output,
    _terminate_subprocess_tree,
    _trim_failure_output,
    run_cmd,
)
from . import common_io as _common_io
from .common_io import cmd_str
from .config import REPO_ROOT, SRC_DIR

# Keep the shared module object and legacy common-io helpers visible so
# existing imports and patch targets keep working after the split.
shutil = _common_io.shutil
for _compat_name in (
    "add_standard_output_arguments",
    "build_env",
    "confirm_or_abort",
    "display_path",
    "emit_output",
    "inject_quality_policy_command",
    "normalize_string_field",
    "normalize_repo_python_shell_command",
    "pipe_output",
    "read_json_object",
    "resolve_repo_python_command",
    "resolve_repo_path",
    "should_emit_output",
    "split_shell_prefix",
    "write_output",
):
    globals()[_compat_name] = getattr(_common_io, _compat_name)
del _compat_name


def find_latest_outcomes_file() -> Path | None:
    """Find the newest mutation `outcomes.json` file under `rust/mutants.out`."""
    return _common_io.find_latest_outcomes_file(src_dir=SRC_DIR)
