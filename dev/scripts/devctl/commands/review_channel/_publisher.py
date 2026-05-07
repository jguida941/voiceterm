"""Publisher and reviewer-supervisor lifecycle helpers for the review-channel command package."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
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
# Auto-poll cadence defaults keyed by operator interaction mode.
# remote_control uses a tighter cadence so the phone-steered operator
# sees near-real-time surface updates without manual refresh.
_AUTO_POLL_CADENCE_DEFAULTS: dict[str, int] = {
    "remote_control": 30,
    "local_terminal": 150,
    "dual_agent": 150,
    "single_agent": 300,
    "unresolved": 150,
}
_DEFAULT_POLL_INTERVAL_SECONDS = 150


@dataclass(frozen=True, slots=True)
class AutoPollCadence:
    """Resolved cadence parameters for follow-loop auto-poll."""

    interval_seconds: int
    operator_interaction_mode: str
    inactivity_timeout_seconds: int


def resolve_auto_poll_cadence(
    *,
    operator_interaction_mode: str = "",
    explicit_interval_seconds: int | None = None,
    explicit_inactivity_timeout_seconds: int | None = None,
) -> AutoPollCadence:
    """Derive follow-loop cadence from typed operator mode.

    Remote-control mode uses a tighter default (30s) so operator surfaces
    stay fresh without manual prompts.  An explicit interval always wins.
    """
    mode = (operator_interaction_mode or "").strip() or "unresolved"
    default_interval = _AUTO_POLL_CADENCE_DEFAULTS.get(
        mode, _DEFAULT_POLL_INTERVAL_SECONDS
    )
    interval = (
        explicit_interval_seconds
        if explicit_interval_seconds is not None
        else default_interval
    )
    inactivity = (
        explicit_inactivity_timeout_seconds
        if explicit_inactivity_timeout_seconds is not None
        else 0
    )
    return AutoPollCadence(
        interval_seconds=max(1, interval),
        operator_interaction_mode=mode,
        inactivity_timeout_seconds=max(0, inactivity),
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
    cadence = resolve_auto_poll_cadence(
        operator_interaction_mode=str(
            getattr(args, "operator_interaction_mode", "") or ""
        ),
        explicit_interval_seconds=(
            int(getattr(args, "follow_interval_seconds", 0) or 0) or None
        ),
        explicit_inactivity_timeout_seconds=(
            int(getattr(args, "follow_inactivity_timeout_seconds", 0) or 0)
        ),
    )
    try:
        interval_idx = command.index("--follow-interval-seconds")
        command[interval_idx + 1] = str(cadence.interval_seconds)
    except (ValueError, IndexError):
        command.extend(
            ["--follow-interval-seconds", str(cadence.interval_seconds)]
        )
    try:
        inactivity_idx = command.index("--follow-inactivity-timeout-seconds")
        command[inactivity_idx + 1] = str(cadence.inactivity_timeout_seconds)
    except (ValueError, IndexError):
        command.extend(
            [
                "--follow-inactivity-timeout-seconds",
                str(cadence.inactivity_timeout_seconds),
            ]
        )

    with log_path.open("a", encoding="utf-8") as handle:
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=handle,
            stderr=handle,
            start_new_session=True,
            env=_spawn_environment("devctl_review_channel_launch", "ensure_follow_publisher"),
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
                invocation_provenance=_failed_start_invocation_provenance(
                    pid=pid or 0,
                    trigger_reason="ensure_follow_publisher_failed_start",
                ),
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
                invocation_provenance=_failed_start_invocation_provenance(
                    pid=pid or 0,
                    trigger_reason="reviewer_supervisor_failed_start",
                ),
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


def _build_reviewer_supervisor_command(
    *,
    repo_root: Path,
    operator_interaction_mode: str = "",
) -> list[str]:
    """Build the reviewer-supervisor subprocess command.

    In remote_control mode the follow interval tightens so operator
    surfaces refresh without manual prompts.
    """
    cadence = resolve_auto_poll_cadence(
        operator_interaction_mode=operator_interaction_mode,
    )
    base = list(REVIEWER_SUPERVISOR_FOLLOW_ARGS)
    # Override interval from cadence when it differs from the constant default.
    try:
        idx = base.index("--follow-interval-seconds")
        base[idx + 1] = str(cadence.interval_seconds)
    except (ValueError, IndexError):
        base.extend(["--follow-interval-seconds", str(cadence.interval_seconds)])
    return [
        sys.executable,
        str((repo_root / "dev/scripts/devctl.py").resolve()),
        *base,
    ]


def spawn_reviewer_supervisor(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    operator_interaction_mode: str = "",
) -> tuple[bool, int | None, str]:
    """Start the reviewer supervisor follow loop as a detached process.

    Accepts ``operator_interaction_mode`` so remote-control sessions
    use a tighter poll cadence and never open a Terminal.app window.
    """
    runtime_paths = _coerce_runtime_paths(paths)

    if runtime_paths.status_dir is None:
        return False, None, "status_dir not resolved"

    log_path = runtime_paths.status_dir / "reviewer_supervisor_follow.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    command = _build_reviewer_supervisor_command(
        repo_root=repo_root,
        operator_interaction_mode=operator_interaction_mode,
    )
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
            env=_spawn_environment("devctl_review_channel_launch", "reviewer_supervisor"),
        )
    return True, process.pid, str(log_path)


def _spawn_environment(daemon_supervisor: str, trigger_reason: str) -> dict[str, str]:
    env = dict(os.environ)
    env["DEVCTL_DAEMON_SUPERVISOR"] = daemon_supervisor
    env.setdefault("DEVCTL_LAUNCHD_LABEL", "")
    env["DEVCTL_TRIGGER_REASON"] = trigger_reason
    return env


def _failed_start_invocation_provenance(
    *,
    pid: int,
    trigger_reason: str,
) -> dict[str, object]:
    return dict(
        (
            ("contract_id", "InvocationProvenance"),
            ("schema_version", 1),
            ("parent_pid", os.getpid()),
            ("process_pid", pid),
            ("launchd_label", os.environ.get("DEVCTL_LAUNCHD_LABEL", "")),
            ("daemon_supervisor", _daemon_supervisor_env()),
            ("trigger_reason", trigger_reason),
            ("command_line", []),
        )
    )


def _daemon_supervisor_env() -> str:
    return os.environ.get(
        "DEVCTL_DAEMON_SUPERVISOR",
        "devctl_review_channel_launch",
    )
