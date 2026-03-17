"""Shared lifecycle persistence helpers for follow-loop controllers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .daemon_events import (
    DaemonEventContext,
    append_daemon_heartbeat,
    append_daemon_stopped,
)
from .lifecycle_state import (
    StoppedLifecycleHeartbeat,
    write_stopped_lifecycle_heartbeat,
)


@dataclass(frozen=True)
class FollowLifecycleContext:
    """Wiring needed to persist one follow loop's lifecycle state."""

    output_root: Path | object
    write_heartbeat_fn: Callable[..., Path]
    heartbeat_factory: Callable[..., object]
    daemon_context: DaemonEventContext
    utc_timestamp_fn: Callable[[], str]


def record_follow_heartbeat(
    *,
    context: FollowLifecycleContext,
    started_at_utc: str,
    snapshots_emitted: int,
    reviewer_mode: str,
) -> None:
    """Persist one follow heartbeat plus its event-log mirror."""
    if not isinstance(context.output_root, Path):
        return
    heartbeat_utc = context.utc_timestamp_fn()
    context.write_heartbeat_fn(
        context.output_root,
        context.heartbeat_factory(
            pid=context.daemon_context.pid,
            started_at_utc=started_at_utc,
            last_heartbeat_utc=heartbeat_utc,
            snapshots_emitted=snapshots_emitted,
            reviewer_mode=reviewer_mode,
        ),
    )
    append_daemon_heartbeat(
        context.daemon_context,
        reviewer_mode=reviewer_mode,
        snapshots_emitted=snapshots_emitted,
        timestamp_utc=heartbeat_utc,
    )


def record_follow_stop(
    *,
    context: FollowLifecycleContext,
    started_at_utc: str,
    snapshots_emitted: int,
    reviewer_mode: str,
    stop_reason: str,
) -> None:
    """Persist final stopped lifecycle state plus its event-log mirror."""
    if not isinstance(context.output_root, Path):
        return
    write_stopped_lifecycle_heartbeat(
        output_root=context.output_root,
        write_heartbeat_fn=context.write_heartbeat_fn,
        heartbeat_factory=context.heartbeat_factory,
        stopped_heartbeat=StoppedLifecycleHeartbeat(
            pid=context.daemon_context.pid,
            started_at_utc=started_at_utc,
            snapshots_emitted=snapshots_emitted,
            reviewer_mode=reviewer_mode,
            stop_reason=stop_reason,
        ),
        utc_timestamp_fn=context.utc_timestamp_fn,
    )
    append_daemon_stopped(
        context.daemon_context,
        reviewer_mode=reviewer_mode,
        snapshots_emitted=snapshots_emitted,
        stop_reason=stop_reason,
    )
