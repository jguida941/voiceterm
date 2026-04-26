"""Shared state/helpers for the event-backed watch-follow runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .event_watch_support import EventWatchContext
from .watch_follow_frames import (
    WatchFollowFrameSpec,
    build_watch_follow_error_report,
    emit_watch_frame,
)


@dataclass(frozen=True)
class WatchFollowRuntimeContext:
    args: object
    repo_root: Path
    review_channel_path: Path
    artifact_paths: object
    target: str
    status_filter: str
    owner: object
    interval: int
    max_snapshots: int
    inactivity_timeout_seconds: int
    deps: object


@dataclass
class WatchFollowLoopState:
    emitted_count: int
    snapshot_seq: int
    frame_seq: int
    prev_signature: object
    last_report: dict[str, object] | None


@dataclass(frozen=True)
class WatchFollowFinishState:
    stop_reason: str
    snapshots_emitted: int
    frame_seq: int
    ok: bool
    errors: list[str] | None = None


def load_initial_watch_bundle(
    ctx: WatchFollowRuntimeContext,
) -> tuple[object | None, list[dict[str, object]] | None, str | None]:
    """Load the first watch bundle and target packet slice."""
    try:
        bundle = ctx.deps.load_or_refresh_event_bundle_fn(
            repo_root=ctx.repo_root,
            review_channel_path=ctx.review_channel_path,
            artifact_paths=ctx.artifact_paths,
        )
        bundle, packets = ctx.deps.load_target_packets_fn(
            context=EventWatchContext(
                args=ctx.args,
                bundle=bundle,
                repo_root=ctx.repo_root,
                review_channel_path=ctx.review_channel_path,
                artifact_paths=ctx.artifact_paths,
            ),
            status_filter=ctx.status_filter,
        )
        return bundle, packets, None
    except (OSError, ValueError) as exc:
        return None, None, str(exc)


def finish_watch_follow(
    ctx: WatchFollowRuntimeContext,
    last_report: dict[str, object] | None,
    outcome: WatchFollowFinishState,
) -> tuple[dict[str, object], int]:
    """Emit the final exit frame and return the terminal watch result."""
    report = dict(last_report or {})
    report.setdefault("command", "review-channel")
    report.setdefault("action", "watch")
    report["ok"] = outcome.ok
    report["snapshots_emitted"] = outcome.snapshots_emitted
    if outcome.errors is not None:
        report["errors"] = list(outcome.errors)
    pipe_rc = 0
    try:
        ctx.deps.write_watch_stop_fn(
            owner=ctx.owner,
            snapshots_emitted=outcome.snapshots_emitted,
            stop_reason=outcome.stop_reason,
            stopped_at_utc=ctx.deps.utc_timestamp_fn(),
        )
        pipe_rc = emit_watch_frame(
            args=ctx.args,
            deps=ctx.deps,
            spec=WatchFollowFrameSpec(
                report=report,
                frame_type="watch_exit",
                frame_seq=outcome.frame_seq,
                target=ctx.target,
                status_filter=ctx.status_filter,
                owner=ctx.owner,
                snapshots_emitted=outcome.snapshots_emitted,
                stop_reason=outcome.stop_reason,
            ),
        )
    finally:
        ctx.deps.release_watch_lifecycle_fn(ctx.owner)
    if pipe_rc != 0:
        return ctx.deps.build_follow_output_error_report_fn(
            action="watch",
            snapshots_emitted=outcome.snapshots_emitted,
            pipe_rc=pipe_rc,
        ), pipe_rc
    if outcome.ok:
        return ctx.deps.build_follow_completion_report_fn(
            action="watch",
            snapshots_emitted=outcome.snapshots_emitted,
            ok=True,
        ), 0
    return build_watch_follow_error_report(
        snapshots_emitted=outcome.snapshots_emitted,
        errors=list(outcome.errors or [f"watch follow stopped: {outcome.stop_reason}"]),
    ), 1
