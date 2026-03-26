"""`devctl review-channel` command implementation.

Orchestrates bridge-backed and event-backed review-channel actions. The
heavy rendering and execution logic lives in the dedicated handler modules:

- review_channel_bridge_handler: launch, rollover, promote, status (bridge)
- review_channel_event_handler: post, watch, inbox, ack, dismiss, apply, history
- review_channel_status: status action, status-context attachers, lifecycle reads
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ...common import emit_output
from ...config import REPO_ROOT
from ...review_channel.context_refs import resolve_context_pack_refs
from ...review_channel.events import event_state_exists
from ...review_channel.follow_controller import EnsureFollowDeps, run_ensure_follow_action
from ...review_channel.follow_stream import (
    build_follow_completion_report,
    build_follow_output_error_report,
    emit_follow_ndjson_frame,
    reset_follow_output,
)
from ...review_channel.reviewer_follow import ReviewerFollowDeps, run_reviewer_follow_action
from ...review_channel.reviewer_state import (
    ReviewerCheckpointUpdate,
    ensure_reviewer_heartbeat,
    reviewer_state_write_to_dict,
    write_reviewer_checkpoint,
    write_reviewer_heartbeat,
)
from ...review_channel.heartbeat import refresh_bridge_heartbeat
from ...review_channel.peer_liveness import reviewer_mode_is_active
from ...review_channel.lifecycle_state import (
    PublisherHeartbeat,
    read_publisher_state,
    read_reviewer_supervisor_state,
    write_publisher_heartbeat,
    write_reviewer_supervisor_heartbeat,
)
from ...review_channel.state import refresh_status_snapshot
from ...time_utils import utc_timestamp
from ..review_channel_bridge_handler import BRIDGE_ACTIONS, _run_bridge_action
from ..review_channel_command.reviewer_support import resolve_checkpoint_instruction
from ..review_channel_command import (
    EVENT_ACTION_SET,
    FAILED_START_HEARTBEAT_FIELDS,
    PUBLISHER_FOLLOW_COMMAND_ARGS,
    PUBLISHER_FOLLOW_LOG_FILENAME,
    PUBLISHER_FOLLOW_OUTPUT_FILENAME,
    REVIEWER_STATE_ACTION_SET,
    REVIEWER_STATE_REPORT_DEFAULTS,
    PublisherLifecycleAssessment,
    ReviewChannelAction,
    RuntimePaths,
    _coerce_action,
    _coerce_runtime_paths,
    _error_report,
    _render_report,
    _resolve_runtime_paths,
    _validate_args,
)
from ..review_channel_event_handler import _run_event_action
from . import ensure as _ensure_mod
from ._bridge_poll import run_bridge_poll_action as _run_bridge_poll_action_impl
from ._render_bridge import run_render_bridge_action as _run_render_bridge_action
from ._wait_actions import (
    run_implementer_wait_action as _run_implementer_wait_action,
    run_reviewer_wait_action as _run_reviewer_wait_action,
)
from .status import (
    _attach_backend_contract,
    _attach_reviewer_worker,
    _attach_status_context,
    _read_publisher_state_safe,
    _read_reviewer_supervisor_state_safe,
    _run_bridge_status,
    _run_status_action,
)

__all__ = [
    "resolve_context_pack_refs",
    "event_state_exists",
    "read_reviewer_supervisor_state",
    "BRIDGE_ACTIONS",
    "_run_bridge_action",
    "_attach_backend_contract",
    "_attach_reviewer_worker",
    "_attach_status_context",
    "_read_publisher_state_safe",
    "_read_reviewer_supervisor_state_safe",
    "_run_bridge_status",
    "_run_status_action",
    "refresh_status_snapshot",
    "run",
]


from ._publisher import ensure_reviewer_supervisor_running as _ensure_reviewer_supervisor_running
from ._publisher import spawn_follow_publisher as _spawn_follow_publisher
from ._publisher import spawn_reviewer_supervisor as _spawn_reviewer_supervisor
from ._publisher import verify_detached_start as _verify_detached_start
from ._publisher import verify_reviewer_supervisor_start as _verify_reviewer_supervisor_start
from ._recover import run_recover_action as _run_recover_action
from ._stop import run_stop_action as _run_stop_action


def _build_ensure_action_deps() -> _ensure_mod.EnsureActionDeps:
    """Bind ensure orchestration to the command-module compatibility seams."""
    return _ensure_mod.EnsureActionDeps(
        run_status_action_fn=lambda *a, **kw: _run_status_action(*a, **kw),
        read_publisher_state_safe_fn=lambda *a, **kw: _read_publisher_state_safe(*a, **kw),
        assess_publisher_lifecycle_fn=lambda *a, **kw: _ensure_mod.assess_publisher_lifecycle(*a, **kw),
        spawn_follow_publisher_fn=lambda *a, **kw: _spawn_follow_publisher(*a, **kw),
        verify_detached_start_fn=lambda *a, **kw: _verify_detached_start(*a, **kw),
        refresh_bridge_heartbeat_fn=lambda *a, **kw: refresh_bridge_heartbeat(*a, **kw),
        reviewer_mode_is_active_fn=lambda value: reviewer_mode_is_active(value),
        run_ensure_follow_action_fn=lambda *a, **kw: _run_ensure_follow_action(*a, **kw),
        spawn_reviewer_supervisor_fn=lambda *a, **kw: _spawn_reviewer_supervisor(*a, **kw),
        verify_reviewer_supervisor_start_fn=lambda *a, **kw: _verify_reviewer_supervisor_start(*a, **kw),
        sleep_fn=lambda seconds: time.sleep(seconds),
    )


def _run_ensure_action(
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


def _run_ensure_follow_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run the persistent ensure-follow publisher."""
    runtime_paths = _coerce_runtime_paths(paths)
    return run_ensure_follow_action(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=ENSURE_FOLLOW_DEPS,
    )


from ._reviewer import build_reviewer_state_report as _build_reviewer_state_report


def _run_reviewer_follow_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Poll reviewer-worker state on cadence."""
    runtime_paths = _coerce_runtime_paths(paths)
    return run_reviewer_follow_action(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=REVIEWER_FOLLOW_DEPS,
    )


from ._reviewer import run_reviewer_state_action as _run_reviewer_state_action_impl


def _run_reviewer_state_action(
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
        run_reviewer_follow_action_fn=_run_reviewer_follow_action,
    )
    auto_start = _ensure_reviewer_supervisor_running(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    if auto_start is not None:
        report["reviewer_supervisor_auto_start"] = auto_start
    return report, exit_code


ENSURE_FOLLOW_DEPS = EnsureFollowDeps(
    ensure_reviewer_heartbeat_fn=lambda *a, **kw: ensure_reviewer_heartbeat(*a, **kw),
    reviewer_state_write_to_dict_fn=lambda *a, **kw: reviewer_state_write_to_dict(*a, **kw),
    run_status_action_fn=lambda *a, **kw: _run_status_action(*a, **kw),
    attach_reviewer_worker_fn=lambda *a, **kw: _attach_reviewer_worker(*a, **kw),
    ensure_reviewer_supervisor_running_fn=lambda *a, **kw: _ensure_reviewer_supervisor_running(*a, **kw),
    emit_follow_ndjson_frame_fn=lambda *a, **kw: emit_follow_ndjson_frame(*a, **kw),
    reset_follow_output_fn=lambda *a, **kw: reset_follow_output(*a, **kw),
    build_follow_completion_report_fn=lambda *a, **kw: build_follow_completion_report(*a, **kw),
    build_follow_output_error_report_fn=lambda *a, **kw: build_follow_output_error_report(*a, **kw),
    write_publisher_heartbeat_fn=lambda *a, **kw: write_publisher_heartbeat(*a, **kw),
    read_publisher_state_fn=lambda *a, **kw: read_publisher_state(*a, **kw),
    utc_timestamp_fn=lambda: utc_timestamp(),
    sleep_fn=lambda seconds: time.sleep(seconds),
)
REVIEWER_FOLLOW_DEPS = ReviewerFollowDeps(
    ensure_reviewer_heartbeat_fn=lambda *a, **kw: ensure_reviewer_heartbeat(*a, **kw),
    build_reviewer_state_report_fn=lambda *a, **kw: _build_reviewer_state_report(*a, **kw),
    reviewer_state_write_to_dict_fn=lambda *a, **kw: reviewer_state_write_to_dict(*a, **kw),
    run_recovery_action_fn=lambda *a, **kw: _run_recover_action(*a, **kw),
    emit_follow_ndjson_frame_fn=lambda *a, **kw: emit_follow_ndjson_frame(*a, **kw),
    reset_follow_output_fn=lambda *a, **kw: reset_follow_output(*a, **kw),
    build_follow_completion_report_fn=lambda *a, **kw: build_follow_completion_report(*a, **kw),
    build_follow_output_error_report_fn=lambda *a, **kw: build_follow_output_error_report(*a, **kw),
    write_reviewer_supervisor_heartbeat_fn=lambda *a, **kw: write_reviewer_supervisor_heartbeat(*a, **kw),
    utc_timestamp_fn=lambda: utc_timestamp(),
    sleep_fn=lambda seconds: time.sleep(seconds),
)


def _dispatch_action(
    *,
    args,
    action: ReviewChannelAction,
    repo_root: Path,
    paths: RuntimePaths,
) -> tuple[dict, int]:
    """Dispatch one validated review-channel action."""
    result: tuple[dict, int]
    if action is ReviewChannelAction.STATUS:
        result = _run_status_action(args=args, repo_root=repo_root, paths=paths)
    elif action is ReviewChannelAction.BRIDGE_POLL:
        result = _run_bridge_poll_action_impl(
            args=args,
            repo_root=repo_root,
            paths=paths,
        )
    elif action is ReviewChannelAction.RENDER_BRIDGE:
        result = _run_render_bridge_action(
            args=args,
            repo_root=repo_root,
            paths=paths,
        )
    elif action is ReviewChannelAction.IMPLEMENTER_WAIT:
        result = _run_implementer_wait_action(
            args=args,
            repo_root=repo_root,
            paths=paths,
            run_status_action_fn=_run_status_action,
        )
    elif action is ReviewChannelAction.REVIEWER_WAIT:
        result = _run_reviewer_wait_action(
            args=args,
            repo_root=repo_root,
            paths=paths,
            run_status_action_fn=_run_status_action,
        )
    elif action in REVIEWER_STATE_ACTION_SET:
        result = _run_reviewer_state_action(
            args=args,
            repo_root=repo_root,
            paths=paths,
        )
    elif action in EVENT_ACTION_SET:
        result = _run_event_action(args=args, repo_root=repo_root, paths=paths)
    elif action is ReviewChannelAction.ENSURE:
        result = _run_ensure_action(args=args, repo_root=repo_root, paths=paths)
    elif action is ReviewChannelAction.STOP:
        result = _run_stop_action(args=args, repo_root=repo_root, paths=paths)
    elif action is ReviewChannelAction.RECOVER:
        result = _run_recover_action(args=args, repo_root=repo_root, paths=paths)
    elif action.value in BRIDGE_ACTIONS or action is ReviewChannelAction.PROMOTE:
        result = _run_bridge_action(args=args, repo_root=repo_root, paths=paths)
    else:
        result = _error_report(
            args,
            f"Unsupported review-channel action: {action.value}",
            exit_code=2,
        )
    return result


def _emit_report_output(args, report: dict[str, object], exit_code: int) -> int:
    """Emit one review-channel report."""
    already_emitted = bool(report.pop("_already_emitted", False))
    if already_emitted:
        return exit_code

    output = json.dumps(report, indent=2) if args.format == "json" else _render_report(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
    )
    if pipe_rc != 0:
        return pipe_rc

    return exit_code


def run(args) -> int:
    """Run one review-channel action."""
    repo_root = REPO_ROOT.resolve()

    try:
        action = _coerce_action(getattr(args, "action", None))
        _validate_args(args, action)
        paths = _resolve_runtime_paths(args, repo_root)
        report, exit_code = _dispatch_action(
            args=args,
            action=action,
            repo_root=repo_root,
            paths=paths,
        )
    except ValueError as exc:
        report, exit_code = _error_report(args, str(exc), exit_code=1)
    except subprocess.CalledProcessError as exc:
        report, exit_code = _error_report(
            args,
            f"launcher subprocess failed: {exc}",
            exit_code=1,
        )
    except OSError as exc:
        report, exit_code = _error_report(args, str(exc), exit_code=1)

    return _emit_report_output(args, report, exit_code)
