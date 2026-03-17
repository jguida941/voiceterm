"""Reducer helpers for daemon lifecycle events in the review-channel event log."""

from __future__ import annotations

from typing import TypedDict

DAEMON_EVENT_TYPES = frozenset({
    "daemon_started",
    "daemon_stopped",
    "daemon_heartbeat",
})

KNOWN_DAEMON_KINDS = frozenset({"publisher", "reviewer_supervisor"})


class DaemonStateDict(TypedDict):
    """Typed shape for one reduced daemon snapshot."""

    running: bool
    pid: int
    started_at_utc: str
    last_heartbeat_utc: str
    snapshots_emitted: int
    reviewer_mode: str
    stop_reason: str
    stopped_at_utc: str


class ReviewRuntimeDict(TypedDict):
    """Typed shape for the reduced runtime section."""

    daemons: dict[str, DaemonStateDict]
    active_daemons: int
    last_daemon_event_utc: str


class DaemonSnapshot:
    """Mutable accumulator for one daemon kind during event reduction."""

    __slots__ = (
        "pid",
        "started_at_utc",
        "last_heartbeat_utc",
        "snapshots_emitted",
        "reviewer_mode",
        "stop_reason",
        "stopped_at_utc",
    )

    def __init__(self) -> None:
        self.pid: int = 0
        self.started_at_utc: str = ""
        self.last_heartbeat_utc: str = ""
        self.snapshots_emitted: int = 0
        self.reviewer_mode: str = ""
        self.stop_reason: str = ""
        self.stopped_at_utc: str = ""

    @property
    def running(self) -> bool:
        active = self.pid and self.started_at_utc and not self.stop_reason
        return bool(active)

    def to_dict(self) -> DaemonStateDict:
        return DaemonStateDict(
            running=self.running,
            pid=self.pid,
            started_at_utc=self.started_at_utc,
            last_heartbeat_utc=self.last_heartbeat_utc,
            snapshots_emitted=self.snapshots_emitted,
            reviewer_mode=self.reviewer_mode,
            stop_reason=self.stop_reason,
            stopped_at_utc=self.stopped_at_utc,
        )


def empty_daemon_state() -> DaemonStateDict:
    """Return a zeroed daemon state dict for kinds with no events yet."""
    return DaemonSnapshot().to_dict()


def build_lifecycle_runtime_state(
    *,
    publisher_state: dict[str, object],
    reviewer_supervisor_state: dict[str, object],
) -> ReviewRuntimeDict:
    """Build runtime truth from persisted lifecycle heartbeat state."""
    publisher_runtime = _daemon_state_from_lifecycle(publisher_state)
    reviewer_supervisor_runtime = _daemon_state_from_lifecycle(
        reviewer_supervisor_state
    )
    daemon_states = (publisher_runtime, reviewer_supervisor_runtime)
    daemon_timestamps = [
        timestamp
        for daemon_state in daemon_states
        for timestamp in (
            daemon_state["stopped_at_utc"],
            daemon_state["last_heartbeat_utc"],
        )
        if timestamp
    ]
    return ReviewRuntimeDict(
        daemons={
            "publisher": publisher_runtime,
            "reviewer_supervisor": reviewer_supervisor_runtime,
        },
        active_daemons=sum(
            1 for daemon_state in daemon_states if daemon_state["running"]
        ),
        last_daemon_event_utc=max(daemon_timestamps, default=""),
    )


def reduce_daemon_event(
    daemon_snapshots: dict[str, DaemonSnapshot],
    event: dict[str, object],
) -> None:
    """Apply one daemon event to the per-kind daemon snapshot accumulator."""
    daemon_kind = str(event.get("daemon_kind") or "").strip()
    if daemon_kind not in KNOWN_DAEMON_KINDS:
        return
    snap = daemon_snapshots.get(daemon_kind)
    if snap is None:
        snap = DaemonSnapshot()
        daemon_snapshots[daemon_kind] = snap
    event_type = str(event.get("event_type") or "").strip()
    timestamp = str(event.get("timestamp_utc") or "")
    if event_type == "daemon_started":
        snap.pid = int(event.get("pid") or 0)
        snap.started_at_utc = timestamp
        snap.last_heartbeat_utc = timestamp
        snap.snapshots_emitted = 0
        snap.reviewer_mode = str(event.get("reviewer_mode") or "")
        snap.stop_reason = ""
        snap.stopped_at_utc = ""
    elif event_type == "daemon_heartbeat":
        snap.last_heartbeat_utc = timestamp
        snap.snapshots_emitted = int(event.get("snapshots_emitted") or snap.snapshots_emitted)
        if event.get("reviewer_mode"):
            snap.reviewer_mode = str(event["reviewer_mode"])
    elif event_type == "daemon_stopped":
        snap.stop_reason = str(event.get("stop_reason") or "unknown")
        snap.stopped_at_utc = timestamp
        snap.snapshots_emitted = int(event.get("snapshots_emitted") or snap.snapshots_emitted)


def build_runtime_state(
    daemon_snapshots: dict[str, DaemonSnapshot],
    last_daemon_event_utc: str,
) -> ReviewRuntimeDict:
    """Build the reduced runtime section from accumulated daemon snapshots."""
    daemons: dict[str, DaemonStateDict] = {}
    active_count = 0
    for kind in sorted(KNOWN_DAEMON_KINDS):
        snap = daemon_snapshots.get(kind)
        if snap is not None:
            daemons[kind] = snap.to_dict()
            if snap.running:
                active_count += 1
        else:
            daemons[kind] = empty_daemon_state()
    return ReviewRuntimeDict(
        daemons=daemons,
        active_daemons=active_count,
        last_daemon_event_utc=last_daemon_event_utc,
    )


def _daemon_state_from_lifecycle(
    lifecycle_state: dict[str, object],
) -> DaemonStateDict:
    """Normalize persisted lifecycle state into the shared runtime shape."""
    return DaemonStateDict(
        running=bool(lifecycle_state.get("running")),
        pid=int(lifecycle_state.get("pid", 0) or 0),
        started_at_utc=str(lifecycle_state.get("started_at_utc") or ""),
        last_heartbeat_utc=str(lifecycle_state.get("last_heartbeat_utc") or ""),
        snapshots_emitted=int(lifecycle_state.get("snapshots_emitted", 0) or 0),
        reviewer_mode=str(lifecycle_state.get("reviewer_mode") or ""),
        stop_reason=str(lifecycle_state.get("stop_reason") or ""),
        stopped_at_utc=str(lifecycle_state.get("stopped_at_utc") or ""),
    )
