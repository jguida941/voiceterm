"""Lifecycle and polling helpers for event-backed watch-follow streams."""

from __future__ import annotations

from .event_watch_support import EventWatchContext
from .watch_follow_frames import (
    WatchFollowFrameSpec,
    emit_watch_frame,
)
from .watch_follow_owner import close_watch_follow_owner, return_output_error
from .watch_follow_state import (
    WatchFollowFinishState,
    WatchFollowLoopState,
    WatchFollowRuntimeContext,
    finish_watch_follow,
    load_initial_watch_bundle,
)


def run_claimed_watch_follow(
    *,
    ctx: WatchFollowRuntimeContext | None = None,
    **legacy_kwargs,
) -> tuple[dict[str, object], int]:
    if ctx is None:
        ctx = WatchFollowRuntimeContext(**legacy_kwargs)
    frame_seq = 0
    emitted_count = 0
    snapshot_seq = 0
    last_report: dict[str, object] | None = None
    stop_reason = "completed"
    try:
        pipe_rc = emit_watch_frame(
            args=ctx.args,
            deps=ctx.deps,
            spec=WatchFollowFrameSpec(
                report=None,
                frame_type="watch_started",
                frame_seq=frame_seq,
                target=ctx.target,
                status_filter=ctx.status_filter,
                owner=ctx.owner,
                snapshots_emitted=0,
            ),
        )
        if pipe_rc != 0:
            return return_output_error(
                deps=ctx.deps,
                owner=ctx.owner,
                pipe_rc=pipe_rc,
                snapshots_emitted=0,
            )
        frame_seq += 1
        if not ctx.deps.watch_parent_is_alive_fn(ctx.owner):
            return finish_watch_follow(
                ctx=ctx,
                last_report=None,
                outcome=WatchFollowFinishState(
                    stop_reason="parent_exit",
                    snapshots_emitted=0,
                    frame_seq=frame_seq,
                    ok=False,
                    errors=["watch parent exited before the initial refresh completed."],
                ),
            )
        bundle, packets, error = load_initial_watch_bundle(ctx)
        if error is not None:
            return finish_watch_follow(
                ctx=ctx,
                last_report=None,
                outcome=WatchFollowFinishState(
                    stop_reason="initial_refresh_failed",
                    snapshots_emitted=0,
                    frame_seq=frame_seq,
                    ok=False,
                    errors=[error],
                ),
            )
        report, _ = ctx.deps.build_event_report_fn(
            args=ctx.args,
            bundle=bundle,
            packets=packets,
        )
        last_report = report
        pipe_rc = emit_watch_frame(
            args=ctx.args,
            deps=ctx.deps,
            spec=WatchFollowFrameSpec(
                report=report,
                frame_type="watch_snapshot",
                frame_seq=frame_seq,
                snapshot_seq=snapshot_seq,
                target=ctx.target,
                status_filter=ctx.status_filter,
                owner=ctx.owner,
                snapshots_emitted=1,
            ),
        )
        if pipe_rc != 0:
            return return_output_error(
                deps=ctx.deps,
                owner=ctx.owner,
                pipe_rc=pipe_rc,
                snapshots_emitted=0,
            )
        emitted_count = 1
        snapshot_seq = 1
        frame_seq += 1
        ctx.deps.write_watch_heartbeat_fn(
            owner=ctx.owner,
            snapshots_emitted=emitted_count,
            heartbeat_utc=ctx.deps.utc_timestamp_fn(),
        )
        prev_signature = ctx.deps.watch_snapshot_signature_fn(
            packets=packets,
            review_state=bundle.review_state,
            target=ctx.target,
        )
        loop_state = WatchFollowLoopState(
            emitted_count=emitted_count,
            snapshot_seq=snapshot_seq,
            frame_seq=frame_seq,
            prev_signature=prev_signature,
            last_report=last_report,
        )
        loop_state, stop_reason = run_watch_follow_loop(ctx=ctx, state=loop_state)
        emitted_count = loop_state.emitted_count
        snapshot_seq = loop_state.snapshot_seq
        frame_seq = loop_state.frame_seq
        last_report = loop_state.last_report
    except KeyboardInterrupt:
        stop_reason = "keyboard_interrupt"
    return finish_watch_follow(
        ctx=ctx,
        last_report=last_report,
        outcome=WatchFollowFinishState(
            stop_reason=stop_reason,
            snapshots_emitted=emitted_count,
            frame_seq=frame_seq,
            ok=stop_reason in {
                "completed",
                "keyboard_interrupt",
                "max_follow_snapshots_reached",
            },
        ),
    )
def run_watch_follow_loop(
    *,
    ctx: WatchFollowRuntimeContext | None = None,
    state: WatchFollowLoopState | None = None,
    **legacy_kwargs,
) -> tuple[WatchFollowLoopState, str]:
    if ctx is None:
        ctx = WatchFollowRuntimeContext(
            args=legacy_kwargs["args"],
            repo_root=legacy_kwargs["repo_root"],
            review_channel_path=legacy_kwargs["review_channel_path"],
            artifact_paths=legacy_kwargs["artifact_paths"],
            target=str(getattr(legacy_kwargs["args"], "target", None) or ""),
            status_filter=legacy_kwargs["status_filter"],
            owner=legacy_kwargs["owner"],
            interval=legacy_kwargs["interval"],
            max_snapshots=legacy_kwargs["max_snapshots"],
            deps=legacy_kwargs["deps"],
        )
    if state is None:
        state = WatchFollowLoopState(
            emitted_count=legacy_kwargs["emitted_count"],
            snapshot_seq=legacy_kwargs["snapshot_seq"],
            frame_seq=legacy_kwargs["frame_seq"],
            prev_signature=legacy_kwargs["prev_signature"],
            last_report=legacy_kwargs["last_report"],
        )
    stop_reason = "completed"
    while ctx.max_snapshots == 0 or state.emitted_count < ctx.max_snapshots:
        ctx.deps.sleep_fn(ctx.interval)
        if not ctx.deps.watch_parent_is_alive_fn(ctx.owner):
            stop_reason = "parent_exit"
            break
        try:
            bundle = ctx.deps.refresh_event_bundle_fn(
                repo_root=ctx.repo_root,
                review_channel_path=ctx.review_channel_path,
                artifact_paths=ctx.artifact_paths,
            )
        except (OSError, ValueError):
            continue
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
        cur_signature = ctx.deps.watch_snapshot_signature_fn(
            packets=packets,
            review_state=bundle.review_state,
            target=ctx.target,
        )
        report, _ = ctx.deps.build_event_report_fn(
            args=ctx.args,
            bundle=bundle,
            packets=packets,
        )
        state.last_report = report
        changed = cur_signature != state.prev_signature
        pipe_rc = emit_watch_frame(
            args=ctx.args,
            deps=ctx.deps,
            spec=WatchFollowFrameSpec(
                report=report,
                frame_type="watch_snapshot" if changed else "watch_heartbeat",
                frame_seq=state.frame_seq,
                snapshot_seq=state.snapshot_seq if changed else None,
                target=str(getattr(ctx.args, "target", None) or ""),
                status_filter=ctx.status_filter,
                owner=ctx.owner,
                snapshots_emitted=state.emitted_count + 1 if changed else state.emitted_count,
            ),
        )
        if pipe_rc != 0:
            close_watch_follow_owner(
                deps=ctx.deps,
                owner=ctx.owner,
                snapshots_emitted=state.emitted_count,
                stop_reason="output_error",
            )
            return state, "output_error"
        if changed:
            state.prev_signature = cur_signature
            state.emitted_count += 1
            state.snapshot_seq += 1
        state.frame_seq += 1
        ctx.deps.write_watch_heartbeat_fn(
            owner=ctx.owner,
            snapshots_emitted=state.emitted_count,
            heartbeat_utc=ctx.deps.utc_timestamp_fn(),
        )
    if (
        stop_reason == "completed"
        and ctx.max_snapshots != 0
        and state.emitted_count >= ctx.max_snapshots
    ):
        stop_reason = "max_follow_snapshots_reached"
    return state, stop_reason
