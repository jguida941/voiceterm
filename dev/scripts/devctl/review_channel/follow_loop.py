"""Shared cadence runner for review-channel follow actions."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from .daemon_events import DaemonEventContext, append_daemon_started
from .follow_lifecycle import (
    FollowLifecycleContext,
    record_follow_heartbeat,
    record_follow_stop,
)


@dataclass(frozen=True)
class FollowLoopTick:
    """One emitted follow snapshot plus its reviewer mode and exit status."""

    report: dict[str, object]
    exit_code: int
    reviewer_mode: str


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


@dataclass(frozen=True)
class FollowLoopSettings:
    """Derived cadence settings for one follow-loop session."""

    interval_seconds: int
    max_snapshots: int
    deadline: float


@dataclass(frozen=True)
class FollowLoopContext:
    """Runtime state shared across loop iterations."""

    args: object
    status_dir: object
    started_at: str
    daemon_context: DaemonEventContext
    lifecycle_context: FollowLifecycleContext


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
    settings = _build_follow_loop_settings(args)
    context = _build_follow_loop_context(
        args=args,
        repo_root=repo_root,
        artifact_paths=artifact_paths,
        status_dir=status_dir,
        plan=plan,
    )
    plan.shared_deps.reset_follow_output_fn(getattr(args, "output", None))
    return _run_loop_iterations(
        context=context,
        settings=settings,
        plan=plan,
    )


def _build_follow_loop_settings(args) -> FollowLoopSettings:
    interval_seconds = max(1, int(getattr(args, "follow_interval_seconds", 120)))
    max_snapshots = getattr(args, "max_follow_snapshots", 0) or 0
    timeout_minutes = getattr(args, "timeout_minutes", 0) or 0
    deadline = (time.monotonic() + timeout_minutes * 60) if timeout_minutes > 0 else 0
    return FollowLoopSettings(
        interval_seconds=interval_seconds,
        max_snapshots=max_snapshots,
        deadline=deadline,
    )


def _build_follow_loop_context(
    *,
    args,
    repo_root: Path,
    artifact_paths: object,
    status_dir: object,
    plan: FollowActionPlan,
) -> FollowLoopContext:
    started_at = plan.shared_deps.utc_timestamp_fn()
    daemon_context = DaemonEventContext(
        repo_root=repo_root,
        artifact_paths=artifact_paths,
        daemon_kind=plan.shape.daemon_kind,
        pid=os.getpid(),
    )
    lifecycle_context = FollowLifecycleContext(
        output_root=status_dir,
        write_heartbeat_fn=plan.shape.write_heartbeat_fn,
        heartbeat_factory=plan.shape.heartbeat_factory,
        daemon_context=daemon_context,
        utc_timestamp_fn=plan.shared_deps.utc_timestamp_fn,
    )
    return FollowLoopContext(
        args=args,
        status_dir=status_dir,
        started_at=started_at,
        daemon_context=daemon_context,
        lifecycle_context=lifecycle_context,
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
    try:
        while settings.max_snapshots == 0 or emitted_count < settings.max_snapshots:
            if settings.deadline and time.monotonic() >= settings.deadline:
                stop_reason = "timed_out"
                break
            tick = plan.build_tick_fn()
            last_mode = tick.reviewer_mode
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
            if settings.deadline and time.monotonic() >= settings.deadline:
                stop_reason = "timed_out"
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
    return result, exit_code
