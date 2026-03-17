"""Lifecycle heartbeat helpers for review-channel publisher/supervisor state."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..repo_packs import active_path_config

DEFAULT_REVIEW_STATUS_DIR_REL = active_path_config().review_status_dir_rel
PUBLISHER_HEARTBEAT_FILENAME = "publisher_heartbeat.json"
PUBLISHER_STALE_AFTER_SECONDS = 300
REVIEWER_SUPERVISOR_HEARTBEAT_FILENAME = "reviewer_supervisor_heartbeat.json"
REVIEWER_SUPERVISOR_STALE_AFTER_SECONDS = 300


@dataclass(frozen=True)
class PublisherHeartbeat:
    """One heartbeat tick from the persistent ensure-follow publisher."""

    pid: int
    started_at_utc: str
    last_heartbeat_utc: str
    snapshots_emitted: int
    reviewer_mode: str
    stop_reason: str = ""
    stopped_at_utc: str = ""


@dataclass(frozen=True)
class ReviewerSupervisorHeartbeat:
    """One heartbeat tick from the reviewer-heartbeat --follow supervisor."""

    pid: int
    started_at_utc: str
    last_heartbeat_utc: str
    snapshots_emitted: int
    reviewer_mode: str
    stop_reason: str = ""
    stopped_at_utc: str = ""


@dataclass(frozen=True)
class StoppedLifecycleHeartbeat:
    """Final lifecycle state written when a follow loop stops."""

    pid: int
    started_at_utc: str
    snapshots_emitted: int
    reviewer_mode: str
    stop_reason: str


def write_publisher_heartbeat(
    output_root: Path,
    heartbeat: PublisherHeartbeat,
) -> Path:
    """Write the publisher heartbeat file for lifecycle consumers."""
    filename = PUBLISHER_HEARTBEAT_FILENAME
    return _write_heartbeat_variants(
        output_root=output_root,
        filename=filename,
        heartbeat=heartbeat,
    )


def read_publisher_state(output_root: Path) -> dict[str, object]:
    """Read publisher lifecycle state from the heartbeat file."""
    filename = PUBLISHER_HEARTBEAT_FILENAME
    return _read_lifecycle_state(
        output_root=output_root,
        filename=filename,
        stale_after_seconds=PUBLISHER_STALE_AFTER_SECONDS,
        missing_detail="No publisher heartbeat file found",
        corrupt_detail="Publisher heartbeat file is corrupt",
    )


def write_reviewer_supervisor_heartbeat(
    output_root: Path,
    heartbeat: ReviewerSupervisorHeartbeat,
) -> Path:
    """Write the reviewer supervisor heartbeat file."""
    filename = REVIEWER_SUPERVISOR_HEARTBEAT_FILENAME
    return _write_heartbeat_variants(
        output_root=output_root,
        filename=filename,
        heartbeat=heartbeat,
    )


def read_reviewer_supervisor_state(output_root: Path) -> dict[str, object]:
    """Read reviewer supervisor lifecycle state from the heartbeat file."""
    filename = REVIEWER_SUPERVISOR_HEARTBEAT_FILENAME
    return _read_lifecycle_state(
        output_root=output_root,
        filename=filename,
        stale_after_seconds=REVIEWER_SUPERVISOR_STALE_AFTER_SECONDS,
        missing_detail="No reviewer supervisor heartbeat file found",
        corrupt_detail="Reviewer supervisor heartbeat file is corrupt",
    )


def _write_heartbeat_variants(
    *,
    output_root: Path,
    filename: str,
    heartbeat: PublisherHeartbeat | ReviewerSupervisorHeartbeat,
) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(heartbeat), indent=2)
    canonical_path = output_root / filename
    canonical_path.write_text(payload, encoding="utf-8")
    instance_path = _instance_heartbeat_path(
        output_root=output_root,
        filename=filename,
        pid=int(getattr(heartbeat, "pid", 0) or 0),
    )
    if instance_path is not None:
        instance_path.write_text(payload, encoding="utf-8")
    return canonical_path


def _read_lifecycle_state(
    *,
    output_root: Path,
    filename: str,
    stale_after_seconds: int,
    missing_detail: str,
    corrupt_detail: str,
) -> dict[str, object]:
    candidate_states: list[tuple[dict[str, object], float]] = []
    existing_paths = [path for path in _heartbeat_candidate_paths(output_root, filename) if path.exists()]
    if not existing_paths:
        return {"running": False, "detail": missing_detail}
    for path in existing_paths:
        data = _load_heartbeat_data(path=path, corrupt_detail=corrupt_detail)
        if not isinstance(data, dict):
            continue
        candidate_states.append(
            (
                _heartbeat_state_from_data(
                    data=data,
                    stale_after_seconds=stale_after_seconds,
                ),
                _heartbeat_sort_timestamp(data=data, path=path),
            )
        )
    if not candidate_states:
        return {"running": False, "detail": corrupt_detail}
    return _select_best_heartbeat_state(candidate_states)


def _heartbeat_candidate_paths(output_root: Path, filename: str) -> list[Path]:
    canonical_path = output_root / filename
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    instance_paths = sorted(output_root.glob(f"{stem}.*{suffix}"))
    return [canonical_path, *[path for path in instance_paths if path != canonical_path]]


def _instance_heartbeat_path(
    *,
    output_root: Path,
    filename: str,
    pid: int,
) -> Path | None:
    if pid <= 0:
        return None
    base = Path(filename)
    return output_root / f"{base.stem}.{pid}{base.suffix}"


def _heartbeat_sort_timestamp(
    *,
    data: dict[str, object],
    path: Path,
) -> float:
    timestamp_str = str(data.get("stopped_at_utc") or data.get("last_heartbeat_utc") or "")
    timestamp = _parse_heartbeat_timestamp(timestamp_str)
    if timestamp is not None:
        return timestamp.timestamp()
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _select_best_heartbeat_state(
    candidate_states: list[tuple[dict[str, object], float]]
) -> dict[str, object]:
    running_candidates = [item for item in candidate_states if bool(item[0].get("running"))]
    selected_pool = running_candidates or candidate_states
    selected_state, _ = max(selected_pool, key=_heartbeat_candidate_sort_key)
    return selected_state


def _heartbeat_candidate_sort_key(
    candidate: tuple[dict[str, object], float]
) -> tuple[float, int, int]:
    state, timestamp = candidate
    snapshots_emitted = int(state.get("snapshots_emitted", 0) or 0)
    pid = int(state.get("pid", 0) or 0)
    return (timestamp, snapshots_emitted, pid)


def _load_heartbeat_data(
    *,
    path: Path,
    corrupt_detail: str,
) -> dict[str, Any] | dict[str, object]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"running": False, "detail": corrupt_detail}
    if not isinstance(loaded, dict):
        return {"running": False, "detail": corrupt_detail}
    return loaded


def _heartbeat_state_from_data(
    *,
    data: dict[str, object],
    stale_after_seconds: int,
) -> dict[str, object]:
    pid = int(data.get("pid", 0) or 0)
    pid_alive = _pid_is_alive(pid)
    last_heartbeat_utc = str(data.get("last_heartbeat_utc", "") or "")
    age_seconds = _heartbeat_age_seconds(last_heartbeat_utc)
    stale = age_seconds is None or age_seconds > stale_after_seconds
    stop_reason = str(data.get("stop_reason", "") or "")
    stopped_at_utc = str(data.get("stopped_at_utc", "") or "")
    if not pid_alive and not stop_reason and pid > 0:
        stop_reason = "detached_exit"
        stopped_at_utc = last_heartbeat_utc
    explicitly_stopped = bool(stop_reason or stopped_at_utc)
    state: dict[str, object] = {}
    state["running"] = not explicitly_stopped and pid_alive and not stale
    state["pid"] = pid
    state["pid_alive"] = pid_alive
    state["stale"] = stale
    state["heartbeat_age_seconds"] = age_seconds
    state["started_at_utc"] = data.get("started_at_utc")
    state["last_heartbeat_utc"] = last_heartbeat_utc
    state["snapshots_emitted"] = data.get("snapshots_emitted", 0)
    state["reviewer_mode"] = data.get("reviewer_mode", "unknown")
    state["stop_reason"] = stop_reason
    state["stopped_at_utc"] = stopped_at_utc
    return state


def write_stopped_lifecycle_heartbeat(
    *,
    output_root: Path | object,
    write_heartbeat_fn,
    heartbeat_factory,
    stopped_heartbeat: StoppedLifecycleHeartbeat,
    utc_timestamp_fn,
) -> None:
    """Persist one explicit stopped-state heartbeat for lifecycle consumers."""
    if not isinstance(output_root, Path):
        return
    stopped_at_utc = utc_timestamp_fn()
    write_heartbeat_fn(
        output_root,
        heartbeat_factory(
            pid=stopped_heartbeat.pid,
            started_at_utc=stopped_heartbeat.started_at_utc,
            last_heartbeat_utc=stopped_at_utc,
            snapshots_emitted=stopped_heartbeat.snapshots_emitted,
            reviewer_mode=stopped_heartbeat.reviewer_mode,
            stop_reason=stopped_heartbeat.stop_reason,
            stopped_at_utc=stopped_at_utc,
        ),
    )


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except (OSError, ProcessLookupError):
        return False


def _heartbeat_age_seconds(timestamp_str: str) -> float | None:
    if not timestamp_str:
        return None
    timestamp = _parse_heartbeat_timestamp(timestamp_str)
    if timestamp is None:
        return None
    return (datetime.now(timezone.utc) - timestamp).total_seconds()


def _parse_heartbeat_timestamp(timestamp_str: str) -> datetime | None:
    if not timestamp_str:
        return None
    try:
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
