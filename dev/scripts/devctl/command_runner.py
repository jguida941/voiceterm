"""Structured command runner used by devctl command surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import time

from .command_runner_process import (
    FAILURE_OUTPUT_MAX_CHARS,
    FAILURE_OUTPUT_MAX_LINES,
    INTERRUPT_KILL_GRACE_SECONDS,
    LIVE_OUTPUT_TIMEOUT_SECONDS,
    POST_EXIT_STDOUT_DRAIN_SECONDS,
    _enqueue_stdout_lines,
    _resolve_live_output_timeout_seconds,
    _run_with_live_output,
    _run_without_live_output,
    _terminate_subprocess_tree,
    _trim_failure_output,
)
from .common_io import cmd_str
from .config import REPO_ROOT


@dataclass(frozen=True)
class CommandRunPolicy:
    live_output: bool = True
    timeout_seconds: float | None = None
    expected_output_patterns: tuple[str, ...] = ()
    forbidden_output_patterns: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommandRunResult:
    name: str
    cmd: list[str]
    cwd: str
    returncode: int
    duration_s: float
    skipped: bool
    error: str = ""
    timeout_seconds: float | None = None
    timed_out: bool = False
    failure_output: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if not self.error:
            payload.pop("error", None)
        if self.timeout_seconds is None:
            payload.pop("timeout_seconds", None)
        if not self.timed_out:
            payload.pop("timed_out", None)
        if not self.failure_output:
            payload.pop("failure_output", None)
        return payload


@dataclass(frozen=True)
class RunnerProgressRecord:
    command_name: str
    phase: str
    status: str
    detail: str = ""
    elapsed_seconds: float = 0.0
    command: tuple[str, ...] = ()


def run_cmd(
    name: str,
    cmd: list[str],
    cwd: Path | None = None,
    env: dict | None = None,
    dry_run: bool = False,
    policy: CommandRunPolicy | None = None,
) -> dict:
    """Run one command and return a result dict instead of raising exceptions."""
    resolved_policy = policy or CommandRunPolicy()
    start = time.time()
    if dry_run:
        print(f"[dry-run] {name}: {cmd_str(cmd)}")
        return CommandRunResult(
            name=name,
            cmd=cmd,
            cwd=str(cwd or REPO_ROOT),
            returncode=0,
            duration_s=0.0,
            skipped=True,
        ).to_dict()

    try:
        _record_progress_event(
            RunnerProgressRecord(
                command_name=name,
                phase="command.start",
                status="started",
                detail=cmd_str(cmd),
                command=tuple(cmd),
            )
        )
        runner = (
            _run_with_live_output
            if resolved_policy.live_output
            else _run_without_live_output
        )
        returncode, output_tail = runner(
            cmd,
            cwd=cwd,
            env=env,
            name=name,
            timeout_seconds=resolved_policy.timeout_seconds,
        )
    except KeyboardInterrupt:
        duration = time.time() - start
        _record_progress_event(
            RunnerProgressRecord(
                command_name=name,
                phase="command.interrupted",
                status="interrupted",
                detail="subprocess tree terminated",
                elapsed_seconds=duration,
                command=tuple(cmd),
            )
        )
        return CommandRunResult(
            name=name,
            cmd=cmd,
            cwd=str(cwd or REPO_ROOT),
            returncode=130,
            duration_s=round(duration, 2),
            skipped=False,
            error="interrupted; subprocess tree terminated",
        ).to_dict()
    except OSError as exc:
        duration = time.time() - start
        _record_progress_event(
            RunnerProgressRecord(
                command_name=name,
                phase="command.error",
                status="failed",
                detail=str(exc),
                elapsed_seconds=duration,
                command=tuple(cmd),
            )
        )
        return CommandRunResult(
            name=name,
            cmd=cmd,
            cwd=str(cwd or REPO_ROOT),
            returncode=127,
            duration_s=round(duration, 2),
            skipped=False,
            error=str(exc),
        ).to_dict()

    duration = time.time() - start
    failure_output = ""
    if returncode != 0:
        failure_output = _trim_failure_output(output_tail)
    _record_progress_event(
        RunnerProgressRecord(
            command_name=name,
            phase=(
                "command.complete"
                if returncode == 0
                else "command.timeout"
                if returncode == 124
                else "command.failed"
            ),
            status="completed" if returncode == 0 else "failed",
            detail=f"returncode={returncode}",
            elapsed_seconds=duration,
            command=tuple(cmd),
        ),
    )
    result = CommandRunResult(
        name=name,
        cmd=cmd,
        cwd=str(cwd or REPO_ROOT),
        returncode=returncode,
        duration_s=round(duration, 2),
        skipped=False,
        timeout_seconds=(
            round(resolved_policy.timeout_seconds, 2)
            if resolved_policy.timeout_seconds is not None
            and resolved_policy.timeout_seconds > 0
            else None
        ),
        timed_out=returncode == 124,
        failure_output=failure_output,
    ).to_dict()
    result["command_output_receipt"] = _build_command_output_receipt_payload(
        name=name,
        cmd=cmd,
        cwd=str(cwd or REPO_ROOT),
        returncode=returncode,
        output_tail=output_tail,
        expected_output_patterns=resolved_policy.expected_output_patterns,
        forbidden_output_patterns=resolved_policy.forbidden_output_patterns,
    )
    return result


def _build_command_output_receipt_payload(
    *,
    name: str,
    cmd: list[str],
    cwd: str,
    returncode: int,
    output_tail: str,
    expected_output_patterns: tuple[str, ...],
    forbidden_output_patterns: tuple[str, ...],
) -> dict[str, object]:
    from .runtime.command_output_receipt import build_command_output_receipt

    return build_command_output_receipt(
        command_name=name,
        command=tuple(cmd),
        cwd=cwd,
        exit_code=returncode,
        stdout=output_tail,
        expected_patterns=expected_output_patterns,
        forbidden_patterns=forbidden_output_patterns,
        capture_scope="tail",
    ).to_dict()


def _record_progress_event(record: RunnerProgressRecord) -> None:
    from .runtime.command_progress import (
        CommandProgressRecord,
        record_command_progress_event,
    )
    from .runtime.stage_progress import StageProgressContext

    record_command_progress_event(
        CommandProgressRecord(
            command_name=record.command_name,
            phase=record.phase,
            status=record.status,
            detail=record.detail,
            elapsed_seconds=record.elapsed_seconds,
            context=StageProgressContext(command=record.command),
        )
    )


__all__ = [
    "FAILURE_OUTPUT_MAX_CHARS",
    "FAILURE_OUTPUT_MAX_LINES",
    "INTERRUPT_KILL_GRACE_SECONDS",
    "LIVE_OUTPUT_TIMEOUT_SECONDS",
    "POST_EXIT_STDOUT_DRAIN_SECONDS",
    "_enqueue_stdout_lines",
    "_resolve_live_output_timeout_seconds",
    "_run_with_live_output",
    "_run_without_live_output",
    "_terminate_subprocess_tree",
    "_trim_failure_output",
    "CommandRunPolicy",
    "CommandRunResult",
    "run_cmd",
]
