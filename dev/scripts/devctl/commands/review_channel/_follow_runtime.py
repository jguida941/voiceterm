"""Runtime bindings for review-channel follow and ensure actions."""

from __future__ import annotations

from collections.abc import Mapping
import time
from pathlib import Path

from ...review_channel.follow_controller import (
    EnsureFollowDeps,
    run_ensure_follow_action as _run_ensure_follow_action_impl,
)
from ...review_channel.follow_stream import (
    build_follow_completion_report,
    build_follow_output_error_report,
    emit_follow_ndjson_frame,
    reset_follow_output,
)
from ...review_channel.heartbeat import refresh_bridge_heartbeat
from ...review_channel.lifecycle_state import (
    read_publisher_state,
    write_publisher_heartbeat,
    write_reviewer_supervisor_heartbeat,
)
from ...review_channel.peer_liveness import reviewer_mode_is_active
from ...review_channel.reviewer_follow import (
    ReviewerFollowDeps,
    run_reviewer_follow_action as _run_reviewer_follow_action_impl,
)
from ...review_channel.reviewer_state import (
    ensure_reviewer_heartbeat,
    reviewer_state_write_to_dict,
)
from ...time_utils import utc_timestamp
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths
from . import ensure as _ensure_mod
from ._publisher import (
    ensure_reviewer_supervisor_running as _ensure_reviewer_supervisor_running,
)
from ._publisher import spawn_follow_publisher as _spawn_follow_publisher
from ._publisher import spawn_reviewer_supervisor as _spawn_reviewer_supervisor
from ._publisher import verify_detached_start as _verify_detached_start
from ._publisher import (
    verify_reviewer_supervisor_start as _verify_reviewer_supervisor_start,
)
from ._recover import run_recover_action as _run_recover_action
from ._reviewer import build_reviewer_state_report as _build_reviewer_state_report
from ._reviewer import run_reviewer_state_action as _run_reviewer_state_action_impl
from .status import _attach_reviewer_worker, _read_publisher_state_safe, _run_status_action


def _build_ensure_action_deps() -> _ensure_mod.EnsureActionDeps:
    """Return command-layer callback bindings for ensure orchestration."""
    return _ensure_mod.EnsureActionDeps(
        run_status_action_fn=_run_status_action,
        read_publisher_state_safe_fn=_read_publisher_state_safe,
        assess_publisher_lifecycle_fn=_ensure_mod.assess_publisher_lifecycle,
        spawn_follow_publisher_fn=_spawn_follow_publisher,
        verify_detached_start_fn=_verify_detached_start,
        refresh_bridge_heartbeat_fn=refresh_bridge_heartbeat,
        reviewer_mode_is_active_fn=reviewer_mode_is_active,
        run_ensure_follow_action_fn=run_ensure_follow_action,
        spawn_reviewer_supervisor_fn=_spawn_reviewer_supervisor,
        verify_reviewer_supervisor_start_fn=_verify_reviewer_supervisor_start,
        sleep_fn=time.sleep,
    )


ENSURE_FOLLOW_DEPS = EnsureFollowDeps(
    ensure_reviewer_heartbeat_fn=ensure_reviewer_heartbeat,
    reviewer_state_write_to_dict_fn=reviewer_state_write_to_dict,
    run_status_action_fn=_run_status_action,
    attach_reviewer_worker_fn=_attach_reviewer_worker,
    ensure_reviewer_supervisor_running_fn=_ensure_reviewer_supervisor_running,
    emit_follow_ndjson_frame_fn=emit_follow_ndjson_frame,
    reset_follow_output_fn=reset_follow_output,
    build_follow_completion_report_fn=build_follow_completion_report,
    build_follow_output_error_report_fn=build_follow_output_error_report,
    write_publisher_heartbeat_fn=write_publisher_heartbeat,
    read_publisher_state_fn=read_publisher_state,
    utc_timestamp_fn=utc_timestamp,
    sleep_fn=time.sleep,
)

REVIEWER_FOLLOW_DEPS = ReviewerFollowDeps(
    ensure_reviewer_heartbeat_fn=ensure_reviewer_heartbeat,
    build_reviewer_state_report_fn=_build_reviewer_state_report,
    reviewer_state_write_to_dict_fn=reviewer_state_write_to_dict,
    run_recovery_action_fn=_run_recover_action,
    emit_follow_ndjson_frame_fn=emit_follow_ndjson_frame,
    reset_follow_output_fn=reset_follow_output,
    build_follow_completion_report_fn=build_follow_completion_report,
    build_follow_output_error_report_fn=build_follow_output_error_report,
    write_reviewer_supervisor_heartbeat_fn=write_reviewer_supervisor_heartbeat,
    utc_timestamp_fn=utc_timestamp,
    sleep_fn=time.sleep,
)


def run_ensure_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run the reviewer-heartbeat ensure flow."""
    return _ensure_mod.run_ensure_action(
        args=args,
        repo_root=repo_root,
        paths=paths,
        deps=_build_ensure_action_deps(),
    )


def run_ensure_follow_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run the persistent ensure-follow publisher."""
    runtime_paths = _coerce_runtime_paths(paths)
    return _run_ensure_follow_action_impl(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=ENSURE_FOLLOW_DEPS,
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
        deps=REVIEWER_FOLLOW_DEPS,
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
    auto_start = _ensure_reviewer_supervisor_running(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    if auto_start is not None:
        report["reviewer_supervisor_auto_start"] = auto_start
    return report, exit_code
