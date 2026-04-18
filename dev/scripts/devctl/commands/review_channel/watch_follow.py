"""Public watch-follow entrypoint for event-backed review-channel watchers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .watch_follow_owner import emit_watch_conflict
from .watch_follow_runtime import run_claimed_watch_follow


@dataclass(frozen=True)
class WatchFollowDeps:
    """Dependency bundle for the event-backed watch-follow loop."""

    validate_follow_json_format_fn: Callable[..., None]
    reset_follow_output_fn: Callable[..., None]
    emit_follow_ndjson_frame_fn: Callable[..., int]
    build_follow_output_error_report_fn: Callable[..., dict[str, object]]
    build_follow_completion_report_fn: Callable[..., dict[str, object]]
    claim_watch_lifecycle_fn: Callable[..., tuple[object | None, object | None]]
    release_watch_lifecycle_fn: Callable[[object], None]
    write_watch_heartbeat_fn: Callable[..., None]
    write_watch_stop_fn: Callable[..., None]
    watch_parent_is_alive_fn: Callable[[object], bool]
    load_or_refresh_event_bundle_fn: Callable[..., object]
    refresh_event_bundle_fn: Callable[..., object]
    load_target_packets_fn: Callable[..., tuple[object, list[dict[str, object]]]]
    watch_snapshot_signature_fn: Callable[..., tuple[frozenset[object], int, str]]
    build_event_report_fn: Callable[..., tuple[dict, int]]
    watch_key_fn: Callable[..., str]
    utc_timestamp_fn: Callable[[], str]
    sleep_fn: Callable[[float], None]


def run_watch_follow(
    *,
    args,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths,
    deps: WatchFollowDeps,
) -> tuple[dict[str, object], int]:
    """Poll the event store and emit explicit watch lifecycle NDJSON frames."""
    deps.validate_follow_json_format_fn(
        action="watch",
        output_format=getattr(args, "format", "json"),
    )
    deps.reset_follow_output_fn(getattr(args, "output", None))
    target = str(getattr(args, "target", None) or "")
    status_filter = getattr(args, "status", None) or "pending"
    owner, conflict = deps.claim_watch_lifecycle_fn(
        artifact_root=Path(artifact_paths.artifact_root),
        target=target,
        status_filter=status_filter,
        started_at_utc=deps.utc_timestamp_fn(),
    )
    if conflict is not None:
        return emit_watch_conflict(
            args=args,
            deps=deps,
            target=target,
            status_filter=status_filter,
            conflict=conflict,
        )
    return run_claimed_watch_follow(
        args=args,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        target=target,
        status_filter=status_filter,
        owner=owner,
        interval=watch_follow_interval_seconds(args),
        max_snapshots=getattr(args, "max_follow_snapshots", 0) or 0,
        deps=deps,
    )


def watch_follow_interval_seconds(args) -> int:
    configured = int(getattr(args, "follow_interval_seconds", 0) or 0)
    if configured > 0:
        return max(1, configured)
    return max(5, (getattr(args, "stale_minutes", 30) * 60) // 6)
