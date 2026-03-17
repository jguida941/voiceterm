"""Reviewer follow-loop helpers for report-only supervisor status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .follow_loop import (
    FollowActionShape,
    FollowLoopTick,
    run_configured_follow_action,
)
from .lifecycle_state import (
    ReviewerSupervisorHeartbeat,
)


@dataclass(frozen=True)
class ReviewerFollowDeps:
    ensure_reviewer_heartbeat_fn: Callable[..., object]
    build_reviewer_state_report_fn: Callable[..., tuple[dict, int]]
    reviewer_state_write_to_dict_fn: Callable[..., dict[str, object] | None]
    emit_follow_ndjson_frame_fn: Callable[..., int]
    reset_follow_output_fn: Callable[..., None]
    build_follow_completion_report_fn: Callable[..., dict[str, object]]
    build_follow_output_error_report_fn: Callable[..., dict[str, object]]
    write_reviewer_supervisor_heartbeat_fn: Callable[..., Path]
    utc_timestamp_fn: Callable[[], str]
    sleep_fn: Callable[[float], None]


def run_reviewer_follow_action(*, args, repo_root: Path, paths: dict[str, object], deps: ReviewerFollowDeps) -> tuple[dict, int]:
    """Poll reviewer-worker state on cadence and emit NDJSON frames."""
    return run_configured_follow_action(
        args=args, repo_root=repo_root, paths=paths, deps_source=deps,
        action=_reviewer_follow_action_shape(deps),
        build_tick_fn=lambda: _build_reviewer_follow_tick(args=args, repo_root=repo_root, paths=paths, deps=deps),
    )


def _reviewer_follow_action_shape(
    deps: ReviewerFollowDeps,
) -> FollowActionShape:
    return FollowActionShape(
        daemon_kind="reviewer_supervisor",
        completion_action="reviewer-heartbeat",
        output_error_action="reviewer-heartbeat",
        write_heartbeat_fn=deps.write_reviewer_supervisor_heartbeat_fn,
        heartbeat_factory=ReviewerSupervisorHeartbeat,
    )


def _build_reviewer_follow_tick(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    deps: ReviewerFollowDeps,
) -> FollowLoopTick:
    bridge_path = paths["bridge_path"]
    assert isinstance(bridge_path, Path)
    ensure_result = deps.ensure_reviewer_heartbeat_fn(
        repo_root=repo_root,
        bridge_path=bridge_path,
        reason="reviewer-follow",
    )
    report, frame_exit_code = deps.build_reviewer_state_report_fn(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    report["reviewer_heartbeat_refreshed"] = ensure_result.refreshed
    _append_follow_error(report, ensure_result.error)
    if ensure_result.state_write is not None:
        report["reviewer_state_write"] = deps.reviewer_state_write_to_dict_fn(
            ensure_result.state_write
        )
    return FollowLoopTick(
        report=report,
        exit_code=frame_exit_code,
        reviewer_mode=ensure_result.reviewer_mode,
    )


def _append_follow_error(report: dict[str, object], error: str | None) -> None:
    if error is None:
        return
    errors = report.setdefault("errors", [])
    if isinstance(errors, list):
        errors.append(error)
