"""Follow-loop helpers for review-channel ensure publisher status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .follow_loop import (
    FollowActionShape,
    FollowLoopTick,
    build_claude_progress_token,
    run_configured_follow_action,
)
from .lifecycle_state import (
    PublisherHeartbeat,
)


@dataclass(frozen=True)
class EnsureFollowDeps:
    ensure_reviewer_heartbeat_fn: Callable[..., object]
    reviewer_state_write_to_dict_fn: Callable[..., dict[str, object] | None]
    run_status_action_fn: Callable[..., tuple[dict, int]]
    attach_reviewer_worker_fn: Callable[..., None]
    emit_follow_ndjson_frame_fn: Callable[..., int]
    reset_follow_output_fn: Callable[..., None]
    build_follow_completion_report_fn: Callable[..., dict[str, object]]
    build_follow_output_error_report_fn: Callable[..., dict[str, object]]
    write_publisher_heartbeat_fn: Callable[..., Path]
    read_publisher_state_fn: Callable[..., dict[str, object]]
    utc_timestamp_fn: Callable[[], str]
    sleep_fn: Callable[[float], None]


def run_ensure_follow_action(*, args, repo_root: Path, paths: dict[str, object], deps: EnsureFollowDeps) -> tuple[dict, int]:
    """Refresh and publish ensure/status frames on cadence."""
    return run_configured_follow_action(
        args=args, repo_root=repo_root, paths=paths, deps_source=deps,
        action=_ensure_follow_action_shape(deps),
        build_tick_fn=lambda: _build_ensure_follow_tick(args=args, repo_root=repo_root, paths=paths, deps=deps),
    )


def _ensure_follow_action_shape(deps: EnsureFollowDeps) -> FollowActionShape:
    return FollowActionShape(
        daemon_kind="publisher",
        completion_action="ensure",
        output_error_action="ensure",
        write_heartbeat_fn=deps.write_publisher_heartbeat_fn,
        heartbeat_factory=PublisherHeartbeat,
    )


def _build_ensure_follow_tick(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    deps: EnsureFollowDeps,
) -> FollowLoopTick:
    bridge_path = paths.get("bridge_path")
    status_dir = paths.get("status_dir")
    assert isinstance(bridge_path, Path)
    progress_token = build_claude_progress_token(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    ensure_result = deps.ensure_reviewer_heartbeat_fn(
        repo_root=repo_root,
        bridge_path=bridge_path,
        reason="ensure-follow",
    )
    report, exit_code = deps.run_status_action_fn(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    if ensure_result.state_write is not None:
        report["reviewer_state_write"] = deps.reviewer_state_write_to_dict_fn(
            ensure_result.state_write
        )
    report["ensure_refreshed"] = ensure_result.refreshed
    if report.get("reviewer_worker") is None:
        deps.attach_reviewer_worker_fn(
            report,
            repo_root=repo_root,
            bridge_path=bridge_path,
        )
    if isinstance(status_dir, Path):
        report["publisher"] = deps.read_publisher_state_fn(status_dir)
    return FollowLoopTick(
        report=report,
        exit_code=exit_code,
        reviewer_mode=ensure_result.reviewer_mode,
        progress_token=progress_token,
    )
