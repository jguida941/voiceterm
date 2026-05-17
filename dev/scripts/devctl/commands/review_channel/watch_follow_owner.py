"""Owner/error helpers for event-backed watch-follow streams."""

from __future__ import annotations

from .watch_follow_frames import (
    build_watch_follow_error_report,
    emit_watch_frame,
)


def emit_watch_conflict(
    *,
    args,
    deps,
    target: str,
    status_filter: str,
    conflict,
) -> tuple[dict[str, object], int]:
    error_report = build_watch_follow_error_report(
        snapshots_emitted=0,
        errors=[
            "watch --follow already has an active owner for "
            f"target={target or 'all'} status={status_filter}"
        ],
    )
    pipe_rc = emit_watch_frame(
        args=args,
        deps=deps,
        report=error_report,
        frame_type="watch_exit",
        frame_seq=0,
        target=target,
        status_filter=status_filter,
        snapshots_emitted=0,
        stop_reason="single_flight_conflict",
        conflict=conflict.owner_state,
        conflict_state_path=conflict.state_path,
    )
    if pipe_rc != 0:
        return deps.build_follow_output_error_report_fn(
            action="watch",
            snapshots_emitted=0,
            pipe_rc=pipe_rc,
        ), pipe_rc
    return error_report, 1


def return_output_error(
    *,
    deps,
    owner,
    pipe_rc: int,
    snapshots_emitted: int,
) -> tuple[dict[str, object], int]:
    close_watch_follow_owner(
        deps=deps,
        owner=owner,
        snapshots_emitted=snapshots_emitted,
        stop_reason="output_error",
    )
    return deps.build_follow_output_error_report_fn(
        action="watch",
        snapshots_emitted=snapshots_emitted,
        pipe_rc=pipe_rc,
    ), pipe_rc


def close_watch_follow_owner(
    *,
    deps,
    owner,
    snapshots_emitted: int,
    stop_reason: str,
) -> None:
    deps.write_watch_stop_fn(
        owner=owner,
        snapshots_emitted=snapshots_emitted,
        stop_reason=stop_reason,
        stopped_at_utc=deps.utc_timestamp_fn(),
    )
    deps.release_watch_lifecycle_fn(owner)
