"""Publisher and reviewer-supervisor lifecycle helpers for the review-channel command package."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

from ...review_channel.lifecycle_state import PublisherHeartbeat, write_publisher_heartbeat
from ...time_utils import utc_timestamp
from ..review_channel_command import (
    FAILED_START_HEARTBEAT_FIELDS,
    PUBLISHER_FOLLOW_COMMAND_ARGS,
    PUBLISHER_FOLLOW_LOG_FILENAME,
    PUBLISHER_FOLLOW_OUTPUT_FILENAME,
    RuntimePaths,
    _coerce_runtime_paths,
)


def spawn_follow_publisher(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[bool, int | None, str]:
    """Start the persistent ensure-follow publisher."""
    runtime_paths = _coerce_runtime_paths(paths)

    if runtime_paths.status_dir is None:
        return False, None, "status_dir not resolved"

    if runtime_paths.bridge_path is None:
        return False, None, "bridge_path not resolved"

    if runtime_paths.review_channel_path is None:
        return False, None, "review_channel_path not resolved"

    output_path = runtime_paths.status_dir / PUBLISHER_FOLLOW_OUTPUT_FILENAME
    log_path = runtime_paths.status_dir / PUBLISHER_FOLLOW_LOG_FILENAME
    log_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str((repo_root / "dev/scripts/devctl.py").resolve()),
        *PUBLISHER_FOLLOW_COMMAND_ARGS,
        "--output",
        str(output_path),
        "--bridge-path",
        os.path.relpath(runtime_paths.bridge_path, repo_root),
        "--review-channel-path",
        os.path.relpath(runtime_paths.review_channel_path, repo_root),
        "--status-dir",
        os.path.relpath(runtime_paths.status_dir, repo_root),
    ]

    with log_path.open("a", encoding="utf-8") as handle:
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=handle,
            stderr=handle,
            start_new_session=True,
        )
    return True, process.pid, str(log_path)


def verify_detached_start(
    *,
    pid: int | None,
    paths: RuntimePaths | Mapping[str, object],
) -> str:
    """Record failed start when a detached publisher exits immediately."""
    from ...review_channel.lifecycle_state import _pid_is_alive

    if pid is not None and _pid_is_alive(pid):
        return "started"

    runtime_paths = _coerce_runtime_paths(paths)
    if runtime_paths.status_dir is not None:
        write_publisher_heartbeat(
            runtime_paths.status_dir,
            PublisherHeartbeat(
                pid=pid or 0,
                started_at_utc=utc_timestamp(),
                last_heartbeat_utc=utc_timestamp(),
                stopped_at_utc=utc_timestamp(),
                **FAILED_START_HEARTBEAT_FIELDS,
            ),
        )

    return "failed_start"


FAILED_SUPERVISOR_START_FIELDS = {
    "snapshots_emitted": 0,
    "stop_reason": "failed_start",
}


def verify_reviewer_supervisor_start(
    *,
    pid: int | None,
    paths: RuntimePaths | Mapping[str, object],
    reviewer_mode: str = "active_dual_agent",
) -> str:
    """Verify a detached reviewer supervisor actually stayed alive.

    Mirrors the publisher verification path: if the PID is dead on arrival,
    persist explicit failed-start lifecycle state.
    """
    from ...review_channel.lifecycle_state import (
        ReviewerSupervisorHeartbeat,
        _pid_is_alive,
        write_reviewer_supervisor_heartbeat,
    )

    if pid is not None and _pid_is_alive(pid):
        return "started"

    runtime_paths = _coerce_runtime_paths(paths)
    if runtime_paths.status_dir is not None:
        write_reviewer_supervisor_heartbeat(
            runtime_paths.status_dir,
            ReviewerSupervisorHeartbeat(
                pid=pid or 0,
                started_at_utc=utc_timestamp(),
                last_heartbeat_utc=utc_timestamp(),
                stopped_at_utc=utc_timestamp(),
                reviewer_mode=reviewer_mode,
                **FAILED_SUPERVISOR_START_FIELDS,
            ),
        )

    return "failed_start"


REVIEWER_SUPERVISOR_FOLLOW_ARGS = [
    "review-channel",
    "--action", "reviewer-heartbeat",
    "--follow",
    "--terminal", "none",
    "--format", "json",
    "--execution-mode", "markdown-bridge",
    "--auto-promote",
    "--follow-interval-seconds", "150",
    "--follow-inactivity-timeout-seconds", "0",
]


def spawn_reviewer_supervisor(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[bool, int | None, str]:
    """Start the reviewer supervisor follow loop as a detached process."""
    runtime_paths = _coerce_runtime_paths(paths)

    if runtime_paths.status_dir is None:
        return False, None, "status_dir not resolved"

    log_path = runtime_paths.status_dir / "reviewer_supervisor_follow.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str((repo_root / "dev/scripts/devctl.py").resolve()),
        *REVIEWER_SUPERVISOR_FOLLOW_ARGS,
    ]
    if runtime_paths.bridge_path is not None:
        command.extend([
            "--bridge-path",
            os.path.relpath(runtime_paths.bridge_path, repo_root),
        ])
    if runtime_paths.status_dir is not None:
        command.extend([
            "--status-dir",
            os.path.relpath(runtime_paths.status_dir, repo_root),
        ])

    with log_path.open("a", encoding="utf-8") as handle:
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=handle,
            stderr=handle,
            start_new_session=True,
        )
    return True, process.pid, str(log_path)


def ensure_reviewer_supervisor_running(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    allow_follow: bool = False,
    sleep_seconds: float = 0.5,
) -> dict[str, object] | None:
    """Keep the detached reviewer supervisor alive for active reviewer mode."""
    from ...review_channel.lifecycle_state import read_reviewer_supervisor_state
    from ...review_channel.peer_liveness import reviewer_mode_is_active
    import time as _time

    if getattr(args, "follow", False) and not allow_follow:
        return None
    if not reviewer_mode_is_active(getattr(args, "reviewer_mode", None)):
        return None

    runtime_paths = _coerce_runtime_paths(paths)
    if runtime_paths.status_dir is None:
        return {"attempted": False, "started": False, "reason": "status_dir_not_resolved"}

    supervisor_state = read_reviewer_supervisor_state(runtime_paths.status_dir)
    if bool(supervisor_state.get("running")):
        return {"attempted": False, "started": False, "reason": "already_running"}

    started, pid, log_path = spawn_reviewer_supervisor(
        args=args, repo_root=repo_root, paths=runtime_paths,
    )
    if not started:
        return {
            "attempted": True, "started": False, "pid": pid,
            "log_path": log_path, "start_status": "spawn_failed",
        }
    _time.sleep(sleep_seconds)
    start_status = verify_reviewer_supervisor_start(
        pid=pid, paths=runtime_paths,
        reviewer_mode=str(getattr(args, "reviewer_mode", "active_dual_agent")),
    )
    return {
        "attempted": True,
        "started": start_status == "started",
        "pid": pid, "log_path": log_path, "start_status": start_status,
    }
