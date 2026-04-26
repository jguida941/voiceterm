"""Frame construction helpers for event-backed watch-follow streams."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...review_channel.watch_lifecycle import WATCHER_KILL_WARNING


@dataclass(frozen=True)
class WatchFollowFrameSpec:
    report: dict[str, object] | None
    frame_type: str
    frame_seq: int
    target: str
    status_filter: str
    snapshots_emitted: int
    owner: object | None = None
    snapshot_seq: int | None = None
    stop_reason: str = ""
    conflict: dict[str, object] | None = None
    conflict_state_path: Path | None = None
    poll_seq: int = 0
    unchanged_polls: int = 0
    awaiting_transition: str = ""


def build_watch_follow_error_report(
    *,
    snapshots_emitted: int,
    errors: list[str],
) -> dict[str, object]:
    report: dict[str, object] = {}
    report["command"] = "review-channel"
    report["action"] = "watch"
    report["ok"] = False
    report["follow"] = True
    report["snapshots_emitted"] = snapshots_emitted
    report["errors"] = list(errors)
    report["_already_emitted"] = True
    return report


def emit_watch_frame(
    *,
    args,
    deps,
    spec: WatchFollowFrameSpec | None = None,
    **legacy_kwargs,
) -> int:
    if spec is None:
        spec = WatchFollowFrameSpec(**legacy_kwargs)
    return deps.emit_follow_ndjson_frame_fn(
        _watch_follow_frame(spec=spec, watch_key_fn=deps.watch_key_fn),
        args=args,
    )


def _watch_follow_frame(
    *,
    spec: WatchFollowFrameSpec | None = None,
    watch_key_fn=None,
    **legacy_kwargs,
) -> dict[str, object]:
    if spec is None:
        spec = WatchFollowFrameSpec(**legacy_kwargs)
    frame = dict(spec.report or {})
    frame["command"] = "review-channel"
    frame["action"] = "watch"
    frame["follow"] = True
    frame["frame_type"] = spec.frame_type
    frame["frame_seq"] = spec.frame_seq
    frame["target"] = spec.target
    frame["status_filter"] = spec.status_filter
    frame["snapshots_emitted"] = spec.snapshots_emitted
    frame["watch_key"] = (
        spec.owner.watch_key
        if spec.owner is not None
        else watch_key_fn(target=spec.target, status_filter=spec.status_filter)
    )
    frame["watcher"] = _watcher_payload(
        owner=spec.owner,
        conflict=spec.conflict,
        conflict_state_path=spec.conflict_state_path,
    )
    if spec.snapshot_seq is not None:
        frame["snapshot_seq"] = spec.snapshot_seq
    if spec.poll_seq:
        frame["poll_seq"] = spec.poll_seq
    if spec.unchanged_polls:
        frame["unchanged_polls"] = spec.unchanged_polls
    if spec.awaiting_transition:
        frame["awaiting_transition"] = spec.awaiting_transition
    if spec.stop_reason:
        frame["stop_reason"] = spec.stop_reason
    if spec.conflict:
        frame["watch_conflict"] = spec.conflict
    return frame


def _watcher_payload(
    *,
    owner=None,
    conflict: dict[str, object] | None = None,
    conflict_state_path: Path | None = None,
) -> dict[str, object]:
    if owner is not None:
        return {
            "pid": owner.pid,
            "state_path": str(owner.state_path),
            "started_at_utc": owner.started_at_utc,
            "stop_command": f"kill {owner.pid}",
            "supervisor_warning": WATCHER_KILL_WARNING,
        }
    conflict = conflict or {}
    pid = int(conflict.get("pid", 0) or 0)
    return {
        "pid": pid,
        "state_path": str(conflict_state_path or ""),
        "started_at_utc": str(conflict.get("started_at_utc") or ""),
        "stop_command": str(conflict.get("stop_command") or f"kill {pid}").strip(),
        "supervisor_warning": str(
            conflict.get("supervisor_warning") or WATCHER_KILL_WARNING
        ).strip(),
    }
