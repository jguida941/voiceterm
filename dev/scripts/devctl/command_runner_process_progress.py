"""Progress bridge helpers for command-runner subprocesses."""

from __future__ import annotations

import subprocess


def _resolve_progress_heartbeat_seconds() -> float:
    from .runtime.command_progress import resolve_progress_heartbeat_seconds

    return resolve_progress_heartbeat_seconds()


def _emit_live_progress_heartbeat(
    *,
    name: str,
    cmd: list[str],
    process: subprocess.Popen,
    started_monotonic: float,
    now: float,
) -> None:
    from .runtime.command_progress import emit_live_progress_heartbeat

    emit_live_progress_heartbeat(
        name=name,
        cmd=cmd,
        process=process,
        started_monotonic=started_monotonic,
        now=now,
    )


def _emit_command_timeout(
    *,
    name: str,
    cmd: list[str],
    process: subprocess.Popen,
    started_monotonic: float,
    timeout_seconds: float,
    message: str,
) -> None:
    from .runtime.command_progress import emit_command_timeout

    emit_command_timeout(
        name=name,
        cmd=cmd,
        process=process,
        started_monotonic=started_monotonic,
        timeout_seconds=timeout_seconds,
        message=message,
    )


__all__ = [
    "_emit_command_timeout",
    "_emit_live_progress_heartbeat",
    "_resolve_progress_heartbeat_seconds",
]
