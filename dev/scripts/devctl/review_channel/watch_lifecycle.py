"""Target-scoped lifecycle ownership for review-channel watch --follow."""

from __future__ import annotations

import fcntl
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TextIO

from .lifecycle_state import _pid_is_alive
from .watch_paths import watch_key, watch_state_path

WATCHER_KILL_WARNING = (
    "Kill only the watcher pid unless you intentionally want to terminate the "
    "launching CLI session."
)


@dataclass(frozen=True)
class WatchLifecycleOwner:
    """One active watcher that currently owns a target/status lane."""

    watch_key: str
    target: str
    status_filter: str
    state_path: Path
    lock_handle: TextIO
    pid: int
    parent_pid: int
    started_at_utc: str


@dataclass(frozen=True)
class WatchLifecycleConflict:
    """Metadata for an already-owned watcher lane."""

    watch_key: str
    state_path: Path
    owner_state: dict[str, object]


@dataclass(frozen=True)
class WatchLifecycleState:
    """One persisted watcher lifecycle snapshot."""

    watch_key: str
    target: str
    status_filter: str
    pid: int
    started_at_utc: str
    last_heartbeat_utc: str
    snapshots_emitted: int
    stop_reason: str
    stopped_at_utc: str
    stop_command: str
    supervisor_warning: str


def claim_watch_lifecycle(
    *,
    artifact_root: Path,
    target: str,
    status_filter: str,
    started_at_utc: str,
) -> tuple[WatchLifecycleOwner | None, WatchLifecycleConflict | None]:
    """Claim exclusive ownership of one watch target/status lane."""
    state_path = watch_state_path(
        artifact_root=artifact_root,
        target=target,
        status_filter=status_filter,
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.touch(exist_ok=True)
    handle = state_path.open("r+", encoding="utf-8")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        owner_state = load_watch_state(state_path)
        handle.close()
        return None, WatchLifecycleConflict(
            watch_key=watch_key(target=target, status_filter=status_filter),
            state_path=state_path,
            owner_state=owner_state,
        )
    owner = WatchLifecycleOwner(
        watch_key=watch_key(target=target, status_filter=status_filter),
        target=target,
        status_filter=status_filter,
        state_path=state_path,
        lock_handle=handle,
        pid=os.getpid(),
        parent_pid=os.getppid(),
        started_at_utc=started_at_utc,
    )
    write_watch_heartbeat(
        owner=owner,
        snapshots_emitted=0,
        heartbeat_utc=started_at_utc,
    )
    return owner, None


def write_watch_heartbeat(
    *,
    owner: WatchLifecycleOwner,
    snapshots_emitted: int,
    heartbeat_utc: str,
) -> None:
    """Persist one active watcher heartbeat under the held single-flight lock."""
    _write_watch_state(
        owner=owner,
        last_heartbeat_utc=heartbeat_utc,
        snapshots_emitted=snapshots_emitted,
        stop_reason="",
        stopped_at_utc="",
    )


def write_watch_stop(
    *,
    owner: WatchLifecycleOwner,
    snapshots_emitted: int,
    stop_reason: str,
    stopped_at_utc: str,
) -> None:
    """Persist the final stopped state before releasing ownership."""
    _write_watch_state(
        owner=owner,
        last_heartbeat_utc=stopped_at_utc,
        snapshots_emitted=snapshots_emitted,
        stop_reason=stop_reason,
        stopped_at_utc=stopped_at_utc,
    )


def release_watch_lifecycle(owner: WatchLifecycleOwner) -> None:
    """Release a claimed watcher lane."""
    try:
        fcntl.flock(owner.lock_handle, fcntl.LOCK_UN)
    finally:
        owner.lock_handle.close()


def watch_parent_is_alive(owner: WatchLifecycleOwner) -> bool:
    """Return False when the launching parent disappeared or was replaced."""
    current_parent_pid = os.getppid()
    if current_parent_pid <= 1 or current_parent_pid != owner.parent_pid:
        return False
    return _pid_is_alive(owner.parent_pid)


def load_watch_state(path: Path) -> dict[str, object]:
    """Best-effort read of one watcher state file."""
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _write_watch_state(
    *,
    owner: WatchLifecycleOwner,
    last_heartbeat_utc: str,
    snapshots_emitted: int,
    stop_reason: str,
    stopped_at_utc: str,
) -> None:
    payload = asdict(
        WatchLifecycleState(
            watch_key=owner.watch_key,
            target=owner.target,
            status_filter=owner.status_filter,
            pid=owner.pid,
            started_at_utc=owner.started_at_utc,
            last_heartbeat_utc=last_heartbeat_utc,
            snapshots_emitted=snapshots_emitted,
            stop_reason=stop_reason,
            stopped_at_utc=stopped_at_utc,
            stop_command=f"kill {owner.pid}",
            supervisor_warning=WATCHER_KILL_WARNING,
        )
    )
    owner.lock_handle.seek(0)
    owner.lock_handle.write(json.dumps(payload, indent=2))
    owner.lock_handle.truncate()
    owner.lock_handle.flush()
