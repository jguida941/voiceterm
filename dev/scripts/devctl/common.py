"""Shared command-runner helpers plus compatibility re-exports for devctl."""

import os
import queue
import signal
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

from . import common_io as _common_io
from .common_io import cmd_str
from .config import REPO_ROOT, SRC_DIR

FAILURE_OUTPUT_MAX_LINES = 60
FAILURE_OUTPUT_MAX_CHARS = 8000
INTERRUPT_KILL_GRACE_SECONDS = 3.0
LIVE_OUTPUT_TIMEOUT_SECONDS = 1800.0
POST_EXIT_STDOUT_DRAIN_SECONDS = 0.1

# Keep the shared module object and legacy common-io helpers visible so
# existing imports and patch targets keep working after the split.
shutil = _common_io.shutil
for _compat_name in (
    "add_standard_output_arguments",
    "build_env",
    "confirm_or_abort",
    "display_path",
    "emit_output",
    "inject_quality_policy_command",
    "normalize_string_field",
    "normalize_repo_python_shell_command",
    "pipe_output",
    "read_json_object",
    "resolve_repo_python_command",
    "resolve_repo_path",
    "should_emit_output",
    "split_shell_prefix",
    "write_output",
):
    globals()[_compat_name] = getattr(_common_io, _compat_name)
del _compat_name


def _trim_failure_output(output_tail: str) -> str:
    """Keep failure excerpts compact so reports stay readable."""
    trimmed = output_tail.strip()
    if len(trimmed) <= FAILURE_OUTPUT_MAX_CHARS:
        return trimmed
    return trimmed[-FAILURE_OUTPUT_MAX_CHARS:]


def _resolve_live_output_timeout_seconds() -> float:
    """Resolve the live-output command timeout from env with safe fallback."""
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
    except BaseException as exc:  # pragma: no cover - reader-thread relay path
        line_queue.put(exc)
    finally:
        line_queue.put(None)


def _run_with_live_output(
    cmd: list[str],
    cwd: Path | None,
    env: dict | None,
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
    timeout_seconds = _resolve_live_output_timeout_seconds()
    deadline = time.monotonic() + timeout_seconds if timeout_seconds > 0 else None
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
                timeout_message = f"command timed out after {timeout_seconds:.0f}s: {cmd_str(cmd)}"
                output_tail.append(timeout_message)
                return 124, "\n".join(output_tail)

            wait_timeout = 0.25
            if parent_exited and post_exit_drain_deadline is not None:
                wait_timeout = max(
                    0.0,
                    min(wait_timeout, post_exit_drain_deadline - time.monotonic()),
                )
            elif deadline is not None:
                wait_timeout = max(0.0, min(wait_timeout, deadline - time.monotonic()))

            try:
                line = line_queue.get(timeout=wait_timeout)
            except queue.Empty:
                if process.poll() is None:
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
        if deadline is None:
            return process.wait(), "\n".join(output_tail)
        remaining = max(0.0, deadline - time.monotonic())
        if remaining <= 0.0:
            _terminate_subprocess_tree(process)
            timeout_message = f"command timed out after {timeout_seconds:.0f}s: {cmd_str(cmd)}"
            output_tail.append(timeout_message)
            return 124, "\n".join(output_tail)
        try:
            return process.wait(timeout=remaining), "\n".join(output_tail)
        except subprocess.TimeoutExpired:
            _terminate_subprocess_tree(process)
            timeout_message = f"command timed out after {timeout_seconds:.0f}s: {cmd_str(cmd)}"
            output_tail.append(timeout_message)
            return 124, "\n".join(output_tail)
    except KeyboardInterrupt:
        _terminate_subprocess_tree(process)
        raise
    finally:
        process.stdout.close()


def _run_without_live_output(
    cmd: list[str],
    cwd: Path | None,
    env: dict | None,
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
    timeout_seconds = _resolve_live_output_timeout_seconds()
    timeout = timeout_seconds if timeout_seconds > 0 else None
    try:
        output_text, _ = process.communicate(timeout=timeout)
        return process.returncode or 0, output_text or ""
    except subprocess.TimeoutExpired:
        _terminate_subprocess_tree(process)
        try:
            output_text, _ = process.communicate(timeout=1)
        except (subprocess.TimeoutExpired, ValueError):
            output_text = ""
        timeout_message = f"command timed out after {timeout_seconds:.0f}s: {cmd_str(cmd)}"
        trimmed = (output_text or "").strip()
        if trimmed:
            return 124, "\n".join([trimmed, timeout_message])
        return 124, timeout_message
    except KeyboardInterrupt:
        _terminate_subprocess_tree(process)
        raise


def _terminate_subprocess_tree(
    process: subprocess.Popen,
    *,
    grace_seconds: float = INTERRUPT_KILL_GRACE_SECONDS,
) -> None:
    """Best-effort process-group teardown used for interrupted local runs."""
    if process.poll() is not None:
        return

    if os.name == "nt":
        process.terminate()
        try:
            process.wait(timeout=grace_seconds)
            return
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        try:
            process.terminate()
        except OSError:
            return
    try:
        process.wait(timeout=grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except OSError:
        try:
            process.kill()
        except OSError:
            return
    process.wait()


def run_cmd(
    name: str,
    cmd: list[str],
    cwd: Path | None = None,
    env: dict | None = None,
    dry_run: bool = False,
    live_output: bool = True,
) -> dict:
    """Run one command and return a result dict instead of raising exceptions."""
    start = time.time()
    if dry_run:
        print(f"[dry-run] {name}: {cmd_str(cmd)}")
        return {
            "name": name,
            "cmd": cmd,
            "cwd": str(cwd or REPO_ROOT),
            "returncode": 0,
            "duration_s": 0.0,
            "skipped": True,
        }

    try:
        runner = _run_with_live_output if live_output else _run_without_live_output
        returncode, output_tail = runner(cmd, cwd=cwd, env=env)
    except KeyboardInterrupt:
        duration = time.time() - start
        return {
            "name": name,
            "cmd": cmd,
            "cwd": str(cwd or REPO_ROOT),
            "returncode": 130,
            "duration_s": round(duration, 2),
            "skipped": False,
            "error": "interrupted; subprocess tree terminated",
        }
    except OSError as exc:
        duration = time.time() - start
        return {
            "name": name,
            "cmd": cmd,
            "cwd": str(cwd or REPO_ROOT),
            "returncode": 127,
            "duration_s": round(duration, 2),
            "skipped": False,
            "error": str(exc),
        }

    duration = time.time() - start
    result = {
        "name": name,
        "cmd": cmd,
        "cwd": str(cwd or REPO_ROOT),
        "returncode": returncode,
        "duration_s": round(duration, 2),
        "skipped": False,
    }
    if returncode != 0:
        failure_output = _trim_failure_output(output_tail)
        if failure_output:
            result["failure_output"] = failure_output
    return result


def find_latest_outcomes_file() -> Path | None:
    """Find the newest mutation `outcomes.json` file under `rust/mutants.out`."""
    return _common_io.find_latest_outcomes_file(src_dir=SRC_DIR)
