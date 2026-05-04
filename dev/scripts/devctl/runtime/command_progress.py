"""Progress helpers used by the shared command runner."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass, field

from .stage_progress import (
    StageProgressContext,
    build_stage_progress_event,
    record_stage_progress_event,
)

PROGRESS_HEARTBEAT_SECONDS = 30.0


@dataclass(frozen=True)
class CommandProgressRecord:
    command_name: str
    phase: str
    status: str
    detail: str = ""
    elapsed_seconds: float = 0.0
    context: StageProgressContext = field(default_factory=StageProgressContext)


def resolve_progress_heartbeat_seconds() -> float:
    """Resolve no-output heartbeat cadence for live child commands."""
    raw = os.getenv("DEVCTL_PROGRESS_HEARTBEAT_SECONDS", "").strip()
    if not raw:
        return PROGRESS_HEARTBEAT_SECONDS
    try:
        cadence = float(raw)
    except ValueError:
        return PROGRESS_HEARTBEAT_SECONDS
    return cadence if cadence > 0 else 0.0


def emit_live_progress_heartbeat(
    *,
    name: str,
    cmd: list[str],
    process: subprocess.Popen,
    started_monotonic: float,
    now: float,
) -> None:
    """Emit a flushed heartbeat for a live child that has produced no output."""
    elapsed = max(0.0, now - started_monotonic)
    detail = f"still running pid={process.pid} elapsed={elapsed:.0f}s"
    if os.environ.get("DEVCTL_NO_PROGRESS") != "1":
        print(
            f"[devctl progress] command={name} status=running detail={detail}",
            file=sys.stderr,
            flush=True,
        )
    record_command_progress_event(
        CommandProgressRecord(
            command_name=name,
            phase="command.heartbeat",
            status="running",
            detail=detail,
            elapsed_seconds=elapsed,
            context=StageProgressContext(
                child_pid=process.pid,
                command=tuple(cmd),
            ),
        )
    )


def emit_command_timeout(
    *,
    name: str,
    cmd: list[str],
    process: subprocess.Popen,
    started_monotonic: float,
    timeout_seconds: float,
    message: str,
) -> None:
    """Emit a flushed timeout event for a child command that exceeded policy."""
    elapsed = max(0.0, time.monotonic() - started_monotonic)
    detail = (
        f"timed out after {timeout_seconds:.0f}s "
        f"pid={process.pid} elapsed={elapsed:.0f}s"
    )
    if os.environ.get("DEVCTL_NO_PROGRESS") != "1":
        print(
            f"[devctl progress] command={name} status=failed detail={detail}",
            file=sys.stderr,
            flush=True,
        )
    record_command_progress_event(
        CommandProgressRecord(
            command_name=name,
            phase="command.timeout",
            status="failed",
            detail=message or detail,
            elapsed_seconds=elapsed,
            context=StageProgressContext(
                child_pid=process.pid,
                command=tuple(cmd),
            ),
        )
    )


def record_command_progress_event(record: CommandProgressRecord) -> None:
    """Best-effort progress artifact writer; command execution never depends on it."""
    try:
        record_stage_progress_event(
            build_stage_progress_event(
                command_name=record.command_name,
                phase=record.phase,
                status=record.status,
                detail=record.detail,
                elapsed_seconds=record.elapsed_seconds,
                context=record.context,
            )
        )
    except (OSError, ValueError, TypeError):
        return


__all__ = [
    "CommandProgressRecord",
    "emit_command_timeout",
    "emit_live_progress_heartbeat",
    "record_command_progress_event",
    "resolve_progress_heartbeat_seconds",
]
