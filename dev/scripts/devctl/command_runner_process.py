"""Process-level helpers for the devctl command runner."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

from .common_io import cmd_str, resolve_repo_python_command
from .command_runner_process_progress import (
    _emit_command_timeout,
    _emit_live_progress_heartbeat,
    _resolve_progress_heartbeat_seconds,
)
from .command_runner_process_tree import (
    INTERRUPT_KILL_GRACE_SECONDS,
    _terminate_subprocess_tree,
)

FAILURE_OUTPUT_MAX_LINES = 60
FAILURE_OUTPUT_MAX_CHARS = 8000
LIVE_OUTPUT_TIMEOUT_SECONDS = 1800.0
POST_EXIT_STDOUT_DRAIN_SECONDS = 0.1


@dataclass(frozen=True)
class LiveProcessExitContext:
    cmd: list[str]
    name: str
    started_monotonic: float
    output_tail: deque[str]


def _trim_failure_output(output_tail: str) -> str:
    """Keep failure excerpts compact so reports stay readable."""
    trimmed = output_tail.strip()
    if len(trimmed) <= FAILURE_OUTPUT_MAX_CHARS:
        return trimmed
    return trimmed[-FAILURE_OUTPUT_MAX_CHARS:]


def _resolve_live_output_timeout_seconds(timeout_seconds: float | None = None) -> float:
    """Resolve the command timeout from explicit policy/env with safe fallback."""
    if timeout_seconds is not None:
        return timeout_seconds if timeout_seconds > 0 else 0.0
    raw = os.getenv("VOICETERM_DEVCTL_LIVE_OUTPUT_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return LIVE_OUTPUT_TIMEOUT_SECONDS
    try:
        timeout = float(raw)
    except ValueError:
        return LIVE_OUTPUT_TIMEOUT_SECONDS
    return timeout if timeout > 0 else 0.0


def _enqueue_stdout_lines(stream, line_queue: "queue.Queue[object]") -> None:
    try:
        for line in stream:
            line_queue.put(line)
    # broad-except: allow reason=reader-thread-relay fallback=queue-exception-to-parent-loop
    except BaseException as exc:  # pragma: no cover - reader-thread relay path
        line_queue.put(exc)
    finally:
        line_queue.put(None)


def _run_with_live_output(
    cmd: list[str],
    cwd: Path | None,
    env: dict | None,
    name: str = "command",
    timeout_seconds: float | None = None,
) -> tuple[int, str]:
    """Stream command output live while retaining a bounded failure excerpt."""
    effective_cmd = resolve_repo_python_command(cmd, cwd=cwd)
    effective_env = dict(os.environ if env is None else env)
    effective_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    process = subprocess.Popen(
        effective_cmd,
        cwd=cwd,
        env=effective_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )
    output_tail: deque[str] = deque(maxlen=FAILURE_OUTPUT_MAX_LINES)
    if process.stdout is None:
        try:
            return process.wait(), ""
        except KeyboardInterrupt:
            _terminate_subprocess_tree(process)
            raise
    resolved_timeout_seconds = _resolve_live_output_timeout_seconds(timeout_seconds)
    deadline = (
        time.monotonic() + resolved_timeout_seconds
        if resolved_timeout_seconds > 0
        else None
    )
    started_monotonic = time.monotonic()
    heartbeat_seconds = _resolve_progress_heartbeat_seconds()
    next_heartbeat = (
        started_monotonic + heartbeat_seconds if heartbeat_seconds > 0 else None
    )
    post_exit_drain_deadline: float | None = None
    line_queue: queue.Queue[object] = queue.Queue()
    reader = threading.Thread(
        target=_enqueue_stdout_lines,
        args=(process.stdout, line_queue),
        daemon=True,
    )
    reader.start()

    try:
        while True:
            parent_exited = process.poll() is not None
            if parent_exited and post_exit_drain_deadline is None:
                post_exit_drain_deadline = time.monotonic() + POST_EXIT_STDOUT_DRAIN_SECONDS

            if parent_exited and line_queue.empty() and (
                not reader.is_alive()
                or (
                    post_exit_drain_deadline is not None
                    and time.monotonic() >= post_exit_drain_deadline
                )
            ):
                break

            if not parent_exited and deadline is not None and time.monotonic() >= deadline:
                _terminate_subprocess_tree(process)
                timeout_message = (
                    f"command timed out after {resolved_timeout_seconds:.0f}s: "
                    f"{cmd_str(cmd)}"
                )
                _emit_command_timeout(
                    name=name,
                    cmd=cmd,
                    process=process,
                    started_monotonic=started_monotonic,
                    timeout_seconds=resolved_timeout_seconds,
                    message=timeout_message,
                )
                output_tail.append(timeout_message)
                return 124, "\n".join(output_tail)

            wait_timeout = _next_wait_timeout(
                parent_exited=parent_exited,
                post_exit_drain_deadline=post_exit_drain_deadline,
                deadline=deadline,
                next_heartbeat=next_heartbeat,
            )
            try:
                line = line_queue.get(timeout=wait_timeout)
            except queue.Empty:
                if process.poll() is None:
                    now = time.monotonic()
                    if next_heartbeat is not None and now >= next_heartbeat:
                        _emit_live_progress_heartbeat(
                            name=name,
                            cmd=cmd,
                            process=process,
                            started_monotonic=started_monotonic,
                            now=now,
                        )
                        next_heartbeat = now + heartbeat_seconds
                    continue

                if post_exit_drain_deadline is None:
                    post_exit_drain_deadline = (
                        time.monotonic() + POST_EXIT_STDOUT_DRAIN_SECONDS
                    )

                if line_queue.empty() and (
                    not reader.is_alive()
                    or time.monotonic() >= post_exit_drain_deadline
                ):
                    break
                continue

            if isinstance(line, BaseException):
                if isinstance(line, KeyboardInterrupt):
                    raise KeyboardInterrupt
                output_tail.append(str(line))
                continue

            if line is None:
                if not reader.is_alive():
                    break
                continue

            print(line, end="")
            output_tail.append(line.rstrip("\n"))
        return _wait_for_live_process_exit(
            process,
            deadline=deadline,
            timeout_seconds=resolved_timeout_seconds,
            context=LiveProcessExitContext(
                cmd=cmd,
                name=name,
                started_monotonic=started_monotonic,
                output_tail=output_tail,
            ),
        )
    except KeyboardInterrupt:
        _terminate_subprocess_tree(process)
        raise
    finally:
        process.stdout.close()


def _next_wait_timeout(
    *,
    parent_exited: bool,
    post_exit_drain_deadline: float | None,
    deadline: float | None,
    next_heartbeat: float | None,
) -> float:
    wait_timeout = 0.25
    if parent_exited and post_exit_drain_deadline is not None:
        wait_timeout = max(
            0.0,
            min(wait_timeout, post_exit_drain_deadline - time.monotonic()),
        )
    elif deadline is not None:
        wait_timeout = max(0.0, min(wait_timeout, deadline - time.monotonic()))
    if next_heartbeat is not None and not parent_exited:
        wait_timeout = max(0.0, min(wait_timeout, next_heartbeat - time.monotonic()))
    return wait_timeout


def _wait_for_live_process_exit(
    process: subprocess.Popen,
    *,
    deadline: float | None,
    timeout_seconds: float,
    context: LiveProcessExitContext,
) -> tuple[int, str]:
    if deadline is None:
        return process.wait(), "\n".join(context.output_tail)
    remaining = max(0.0, deadline - time.monotonic())
    if remaining <= 0.0:
        _terminate_subprocess_tree(process)
        timeout_message = (
            f"command timed out after {timeout_seconds:.0f}s: "
            f"{cmd_str(context.cmd)}"
        )
        _emit_command_timeout(
            name=context.name,
            cmd=context.cmd,
            process=process,
            started_monotonic=context.started_monotonic,
            timeout_seconds=timeout_seconds,
            message=timeout_message,
        )
        context.output_tail.append(timeout_message)
        return 124, "\n".join(context.output_tail)
    try:
        return process.wait(timeout=remaining), "\n".join(context.output_tail)
    except subprocess.TimeoutExpired:
        _terminate_subprocess_tree(process)
        timeout_message = (
            f"command timed out after {timeout_seconds:.0f}s: "
            f"{cmd_str(context.cmd)}"
        )
        _emit_command_timeout(
            name=context.name,
            cmd=context.cmd,
            process=process,
            started_monotonic=context.started_monotonic,
            timeout_seconds=timeout_seconds,
            message=timeout_message,
        )
        context.output_tail.append(timeout_message)
        return 124, "\n".join(context.output_tail)


def _run_without_live_output(
    cmd: list[str],
    cwd: Path | None,
    env: dict | None,
    name: str = "command",
    timeout_seconds: float | None = None,
) -> tuple[int, str]:
    """Run a command quietly while retaining combined stdout/stderr text."""
    effective_cmd = resolve_repo_python_command(cmd, cwd=cwd)
    effective_env = dict(os.environ if env is None else env)
    effective_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    process = subprocess.Popen(
        effective_cmd,
        cwd=cwd,
        env=effective_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    resolved_timeout_seconds = _resolve_live_output_timeout_seconds(timeout_seconds)
    timeout = resolved_timeout_seconds if resolved_timeout_seconds > 0 else None
    started_monotonic = time.monotonic()
    try:
        output_text, _ = process.communicate(timeout=timeout)
        return process.returncode or 0, output_text or ""
    except subprocess.TimeoutExpired:
        _terminate_subprocess_tree(process)
        try:
            output_text, _ = process.communicate(timeout=1)
        except (subprocess.TimeoutExpired, ValueError):
            output_text = ""
        timeout_message = (
            f"command timed out after {resolved_timeout_seconds:.0f}s: {cmd_str(cmd)}"
        )
        _emit_command_timeout(
            name=name,
            cmd=cmd,
            process=process,
            started_monotonic=started_monotonic,
            timeout_seconds=resolved_timeout_seconds,
            message=timeout_message,
        )
        trimmed = (output_text or "").strip()
        if trimmed:
            return 124, "\n".join([trimmed, timeout_message])
        return 124, timeout_message
    except KeyboardInterrupt:
        _terminate_subprocess_tree(process)
        raise
