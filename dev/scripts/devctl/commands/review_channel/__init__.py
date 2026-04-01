"""`devctl review-channel` command implementation.

Orchestrates bridge-backed and event-backed review-channel actions. The
heavy rendering and execution logic lives in the dedicated handler modules:

- review_channel.bridge_handler: launch, rollover, promote, status (bridge)
- review_channel_event_handler: post, watch, inbox, ack, dismiss, apply, history
- review_channel_status: status action, status-context attachers, lifecycle reads
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from ...common import emit_output
from ...config import REPO_ROOT
from ...review_channel.context_refs import resolve_context_pack_refs
from ...review_channel.events import event_state_exists
from ...review_channel.follow_controller import (
    EnsureFollowDeps,
    run_ensure_follow_action as _run_ensure_follow_action_impl,
)
from ...review_channel.follow_stream import (
    build_follow_completion_report,
    build_follow_output_error_report,
)
from ...review_channel.heartbeat import refresh_bridge_heartbeat
from ...review_channel.lifecycle_state import (
    read_reviewer_supervisor_state,
    write_reviewer_supervisor_heartbeat,
)
from ...review_channel.peer_liveness import reviewer_mode_is_active
from ...review_channel.reviewer_follow import (
    ReviewerFollowDeps,
    run_reviewer_follow_action as _run_reviewer_follow_action_impl,
)
from ...review_channel.reviewer_state import reviewer_state_write_to_dict
from ...review_channel.state import refresh_status_snapshot
from ...time_utils import utc_timestamp
from .bridge_handler import BRIDGE_ACTIONS, _run_bridge_action
from . import ensure as _ensure_mod
from ..review_channel_command import (
    EVENT_ACTION_SET,
    PublisherLifecycleAssessment,
    REVIEWER_STATE_ACTION_SET,
    ReviewChannelAction,
    RuntimePaths,
    _coerce_action,
    _error_report,
    _render_report,
    _resolve_runtime_paths,
    _validate_args,
)
from ..review_channel_event_handler import _run_event_action
from ._bridge_poll import run_bridge_poll_action as _run_bridge_poll_action_impl
from ._follow_runtime import (
    _build_reviewer_state_report,
    _ensure_reviewer_supervisor_running,
    _spawn_follow_publisher,
    _spawn_reviewer_supervisor,
    _verify_detached_start,
    _verify_reviewer_supervisor_start,
    emit_follow_ndjson_frame,
    ensure_reviewer_heartbeat,
    read_publisher_state,
    reset_follow_output,
    write_publisher_heartbeat,
)
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
    "PublisherLifecycleAssessment",
    "_run_bridge_action",
    "_attach_backend_contract",
    "_attach_reviewer_worker",
    "_attach_status_context",
    "_build_reviewer_state_report",
    "_ensure_reviewer_supervisor_running",
    "_read_publisher_state_safe",
    "_read_reviewer_supervisor_state_safe",
    "_spawn_follow_publisher",
    "_spawn_reviewer_supervisor",
    "_run_bridge_status",
    "_verify_detached_start",
    "_verify_reviewer_supervisor_start",
    "_run_ensure_action",
    "_run_reviewer_follow_action",
    "_run_reviewer_state_action",
    "_run_status_action",
    "emit_follow_ndjson_frame",
    "ensure_reviewer_heartbeat",
    "read_publisher_state",
    "refresh_status_snapshot",
    "reset_follow_output",
    "run",
    "time",
    "write_publisher_heartbeat",
]

from ._recover import run_recover_action as _run_recover_action
from ._reset_implementer import (
    run_reset_implementer_state_action as _run_reset_implementer_state_action,
)
from ._reviewer import run_reviewer_state_action as _run_reviewer_state_action_impl
from ._stop import run_stop_action as _run_stop_action


def _build_root_ensure_follow_deps() -> EnsureFollowDeps:
    """Resolve ensure-follow deps through the package root for compatibility patches."""

    return EnsureFollowDeps(
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


def _build_root_reviewer_follow_deps() -> ReviewerFollowDeps:
    """Resolve reviewer-follow deps through the package root for compatibility patches."""

    return ReviewerFollowDeps(
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


def _run_ensure_follow_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
) -> tuple[dict, int]:
    """Run ensure-follow with package-root dependency bindings."""

    return _run_ensure_follow_action_impl(
        args=args,
        repo_root=repo_root,
        paths=paths,
        deps=_build_root_ensure_follow_deps(),
    )


def _run_reviewer_follow_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
) -> tuple[dict, int]:
    """Run reviewer-follow with package-root dependency bindings."""

    return _run_reviewer_follow_action_impl(
        args=args,
        repo_root=repo_root,
        paths=paths,
        deps=_build_root_reviewer_follow_deps(),
    )


def _run_ensure_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
) -> tuple[dict, int]:
    """Run ensure with package-root dependency bindings."""

    return _ensure_mod.run_ensure_action(
        args=args,
        repo_root=repo_root,
        paths=paths,
        deps=_ensure_mod.EnsureActionDeps(
            run_status_action_fn=_run_status_action,
            read_publisher_state_safe_fn=_read_publisher_state_safe,
            assess_publisher_lifecycle_fn=_ensure_mod.assess_publisher_lifecycle,
            spawn_follow_publisher_fn=_spawn_follow_publisher,
            verify_detached_start_fn=_verify_detached_start,
            refresh_bridge_heartbeat_fn=refresh_bridge_heartbeat,
            reviewer_mode_is_active_fn=reviewer_mode_is_active,
            run_ensure_follow_action_fn=_run_ensure_follow_action,
            spawn_reviewer_supervisor_fn=_spawn_reviewer_supervisor,
            verify_reviewer_supervisor_start_fn=_verify_reviewer_supervisor_start,
            sleep_fn=time.sleep,
        ),
    )


def _run_reviewer_state_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
) -> tuple[dict, int]:
    """Run reviewer-state actions with package-root follow bindings."""

    return _run_reviewer_state_action_impl(
        args=args,
        repo_root=repo_root,
        paths=paths,
        run_reviewer_follow_action_fn=_run_reviewer_follow_action,
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
    elif action is ReviewChannelAction.RESET_IMPLEMENTER_STATE:
        result = _run_reset_implementer_state_action(
            args=args,
            repo_root=repo_root,
            paths=paths,
            run_status_action_fn=_run_status_action,
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
