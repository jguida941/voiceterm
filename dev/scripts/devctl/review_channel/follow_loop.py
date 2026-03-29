"""Shared cadence runner for review-channel follow actions."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from .daemon_events import append_daemon_started
from .follow_lifecycle import record_follow_heartbeat, record_follow_stop
from .follow_loop_support import (
    FollowLoopContext,
    FollowLoopContextInputs,
    FollowLoopSettings,
    build_claude_progress_token,
    build_follow_loop_context,
    build_follow_loop_settings,
)

SELF_ASSIGNMENT_DUE_POLLS = 3
STALL_ESCALATION_POLLS = 6


@dataclass(frozen=True)
class FollowLoopTick:
    """One emitted follow snapshot plus its reviewer mode and exit status."""

    report: dict[str, object]
    exit_code: int
    reviewer_mode: str
    progress_token: str = ""


class FollowLoopSharedDepSource(Protocol):
    """Attribute contract for follow actions that share runner behavior."""

    emit_follow_ndjson_frame_fn: Callable[..., int]
    reset_follow_output_fn: Callable[..., None]
    build_follow_completion_report_fn: Callable[..., dict[str, object]]
    build_follow_output_error_report_fn: Callable[..., dict[str, object]]
    utc_timestamp_fn: Callable[[], str]
    sleep_fn: Callable[[float], None]


@dataclass(frozen=True)
class FollowLoopSharedDeps:
    """Shared side effects for all follow-loop actions."""

    emit_follow_ndjson_frame_fn: Callable[..., int]
    reset_follow_output_fn: Callable[..., None]
    build_follow_completion_report_fn: Callable[..., dict[str, object]]
    build_follow_output_error_report_fn: Callable[..., dict[str, object]]
    utc_timestamp_fn: Callable[[], str]
    sleep_fn: Callable[[float], None]

    @classmethod
    def from_source(
        cls,
        source: FollowLoopSharedDepSource,
    ) -> "FollowLoopSharedDeps":
        """Build shared follow deps from a controller-specific dep bundle."""
        return cls(
            emit_follow_ndjson_frame_fn=source.emit_follow_ndjson_frame_fn,
            reset_follow_output_fn=source.reset_follow_output_fn,
            build_follow_completion_report_fn=source.build_follow_completion_report_fn,
            build_follow_output_error_report_fn=source.build_follow_output_error_report_fn,
            utc_timestamp_fn=source.utc_timestamp_fn,
            sleep_fn=source.sleep_fn,
        )


@dataclass(frozen=True)
class FollowActionShape:
    """Action-specific lifecycle identity for the shared follow runner."""

    daemon_kind: str
    completion_action: str
    output_error_action: str
    write_heartbeat_fn: Callable[..., Path]
    heartbeat_factory: type[object]


@dataclass(frozen=True)
class FollowActionPlan:
    """Executable follow action plan."""

    shape: FollowActionShape
    build_tick_fn: Callable[[], FollowLoopTick]
    shared_deps: FollowLoopSharedDeps


def run_configured_follow_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    action: FollowActionShape,
    build_tick_fn: Callable[[], FollowLoopTick],
    deps_source: FollowLoopSharedDepSource,
) -> tuple[dict, int]:
    """Build a follow action plan and execute the shared loop."""
    return run_follow_loop(
        args=args,
        repo_root=repo_root,
        paths=paths,
        plan=FollowActionPlan(
            shape=action,
            build_tick_fn=build_tick_fn,
            shared_deps=FollowLoopSharedDeps.from_source(deps_source),
        ),
    )


def run_follow_loop(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    plan: FollowActionPlan,
) -> tuple[dict, int]:
    """Refresh follow snapshots on cadence and persist lifecycle state."""
    artifact_paths = paths.get("artifact_paths")
    status_dir = paths.get("status_dir")
    settings = build_follow_loop_settings(args)
    context = build_follow_loop_context(
        FollowLoopContextInputs(
            args=args,
            repo_root=repo_root,
            artifact_paths=artifact_paths,
            status_dir=status_dir,
            daemon_kind=plan.shape.daemon_kind,
            write_heartbeat_fn=plan.shape.write_heartbeat_fn,
            heartbeat_factory=plan.shape.heartbeat_factory,
            utc_timestamp_fn=plan.shared_deps.utc_timestamp_fn,
        )
    )
    plan.shared_deps.reset_follow_output_fn(getattr(args, "output", None))
    return _run_loop_iterations(
        context=context,
        settings=settings,
        plan=plan,
    )


def _run_loop_iterations(
    *,
    context: FollowLoopContext,
    settings: FollowLoopSettings,
    plan: FollowActionPlan,
) -> tuple[dict, int]:
    stop_reason = "completed"
    emitted_count = 0
    seq = 0
    exit_code = 0
    last_mode = "unknown"
    started_event_emitted = False
    last_progress_token = ""
    last_progress_monotonic: float | None = None
    unchanged_progress_polls = 0
    max_unchanged_progress_polls = 0
    try:
        while settings.max_snapshots == 0 or emitted_count < settings.max_snapshots:
            now_monotonic = time.monotonic()
            if settings.deadline and now_monotonic >= settings.deadline:
                stop_reason = "timed_out"
                break
            if (
                settings.inactivity_timeout_seconds > 0
                and last_progress_monotonic is not None
                and (
                    now_monotonic - last_progress_monotonic
                    >= settings.inactivity_timeout_seconds
                )
            ):
                stop_reason = "inactivity_timeout"
                break
            tick = plan.build_tick_fn()
            last_mode = tick.reviewer_mode
            progress_token = tick.progress_token.strip()
            progress_changed = bool(progress_token) and progress_token != last_progress_token
            if progress_changed:
                last_progress_token = progress_token
                last_progress_monotonic = now_monotonic
                unchanged_progress_polls = 0
            else:
                unchanged_progress_polls += 1
                if (
                    settings.inactivity_timeout_seconds > 0
                    and last_progress_monotonic is None
                ):
                    # Start the inactivity clock even when progress token is empty
                    # so the timeout fires instead of hanging forever on read failures.
                    last_progress_monotonic = now_monotonic
            max_unchanged_progress_polls = max(
                max_unchanged_progress_polls,
                unchanged_progress_polls,
            )
            if not started_event_emitted:
                append_daemon_started(
                    context.daemon_context,
                    reviewer_mode=last_mode,
                    timestamp_utc=context.started_at,
                )
                started_event_emitted = True
            if isinstance(context.status_dir, Path):
                record_follow_heartbeat(
                    context=context.lifecycle_context,
                    started_at_utc=context.started_at,
                    snapshots_emitted=emitted_count + 1,
                    reviewer_mode=last_mode,
                )
            frame = dict(tick.report)
            frame["follow"] = True
            frame["snapshot_seq"] = seq
            frame["claude_unchanged_polls"] = unchanged_progress_polls
            frame["claude_self_assignment_due"] = (
                unchanged_progress_polls >= SELF_ASSIGNMENT_DUE_POLLS
            )
            frame["claude_progress_stalled"] = (
                unchanged_progress_polls >= STALL_ESCALATION_POLLS
            )
            pipe_rc = plan.shared_deps.emit_follow_ndjson_frame_fn(frame, args=context.args)
            exit_code = max(exit_code, tick.exit_code)
            if pipe_rc != 0:
                stop_reason = "output_error"
                record_follow_stop(
                    context=context.lifecycle_context,
                    started_at_utc=context.started_at,
                    snapshots_emitted=emitted_count,
                    reviewer_mode=last_mode,
                    stop_reason=stop_reason,
                )
                return (
                    plan.shared_deps.build_follow_output_error_report_fn(
                        action=plan.shape.output_error_action,
                        snapshots_emitted=emitted_count,
                        pipe_rc=pipe_rc,
                    ),
                    pipe_rc,
                )
            emitted_count += 1
            seq += 1
            if settings.max_snapshots != 0 and emitted_count >= settings.max_snapshots:
                break
            now_monotonic = time.monotonic()
            if settings.deadline and now_monotonic >= settings.deadline:
                stop_reason = "timed_out"
                break
            if (
                settings.inactivity_timeout_seconds > 0
                and last_progress_monotonic is not None
                and (
                    now_monotonic - last_progress_monotonic
                    >= settings.inactivity_timeout_seconds
                )
            ):
                stop_reason = "inactivity_timeout"
                break
            plan.shared_deps.sleep_fn(settings.interval_seconds)
    except KeyboardInterrupt:
        stop_reason = "manual_stop"

    record_follow_stop(
        context=context.lifecycle_context,
        started_at_utc=context.started_at,
        snapshots_emitted=emitted_count,
        reviewer_mode=last_mode,
        stop_reason=stop_reason,
    )
    result = plan.shared_deps.build_follow_completion_report_fn(
        action=plan.shape.completion_action,
        snapshots_emitted=emitted_count,
        ok=exit_code == 0,
        reviewer_mode=last_mode,
    )
    result["stop_reason"] = stop_reason
    result["max_claude_unchanged_polls"] = max_unchanged_progress_polls
    result["claude_self_assignment_due"] = (
        max_unchanged_progress_polls >= SELF_ASSIGNMENT_DUE_POLLS
    )
    result["claude_progress_stalled"] = (
        max_unchanged_progress_polls >= STALL_ESCALATION_POLLS
    )
    return result, exit_code
