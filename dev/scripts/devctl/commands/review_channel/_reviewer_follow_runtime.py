"""Runtime bindings for reviewer follow and reviewer-state actions."""

from __future__ import annotations

from collections.abc import Mapping
import time
from pathlib import Path

from ...review_channel.reviewer_follow import (
    ReviewerFollowDeps,
    run_reviewer_follow_action as _run_reviewer_follow_action_impl,
)
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths
from ._reviewer import run_reviewer_state_action as _run_reviewer_state_action_impl


def _build_reviewer_follow_deps() -> ReviewerFollowDeps:
    """Return late-bound reviewer follow deps so tests can patch the compat surface."""
    from . import _follow_runtime as compat_runtime

    return ReviewerFollowDeps(
        ensure_reviewer_heartbeat_fn=compat_runtime.ensure_reviewer_heartbeat,
        build_reviewer_state_report_fn=compat_runtime._build_reviewer_state_report,
        reviewer_state_write_to_dict_fn=compat_runtime.reviewer_state_write_to_dict,
        run_recovery_action_fn=compat_runtime._run_recover_action,
        run_rollover_action_fn=compat_runtime._run_bridge_action,
        emit_follow_ndjson_frame_fn=compat_runtime.emit_follow_ndjson_frame,
        reset_follow_output_fn=compat_runtime.reset_follow_output,
        build_follow_completion_report_fn=(
            compat_runtime.build_follow_completion_report
        ),
        build_follow_output_error_report_fn=(
            compat_runtime.build_follow_output_error_report
        ),
        write_reviewer_supervisor_heartbeat_fn=(
            compat_runtime.write_reviewer_supervisor_heartbeat
        ),
        utc_timestamp_fn=compat_runtime.utc_timestamp,
        sleep_fn=time.sleep,
    )


def run_reviewer_follow_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Poll reviewer-worker state on cadence."""
    runtime_paths = _coerce_runtime_paths(paths)
    return _run_reviewer_follow_action_impl(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=_build_reviewer_follow_deps(),
    )


def run_reviewer_state_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run one reviewer heartbeat/checkpoint write."""
    report, exit_code = _run_reviewer_state_action_impl(
        args=args,
        repo_root=repo_root,
        paths=paths,
        run_reviewer_follow_action_fn=run_reviewer_follow_action,
    )
    from . import _follow_runtime as compat_runtime

    auto_start = compat_runtime._ensure_reviewer_supervisor_running(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    if auto_start is not None:
        report["reviewer_supervisor_auto_start"] = auto_start
    return report, exit_code
