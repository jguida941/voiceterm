"""Shared helper functions used across devctl commands."""

from collections import deque
import os
import signal
import shutil
import subprocess
import time
from pathlib import Path
from typing import Deque, List, Optional, Tuple

from .config import REPO_ROOT, SRC_DIR

FAILURE_OUTPUT_MAX_LINES = 60
FAILURE_OUTPUT_MAX_CHARS = 8000
INTERRUPT_KILL_GRACE_SECONDS = 3.0


def cmd_str(cmd: List[str]) -> str:
    """Render a command list as a printable string."""
    return " ".join(cmd)


def _trim_failure_output(output_tail: str) -> str:
    """Keep failure excerpts compact so reports stay readable."""
    trimmed = output_tail.strip()
    if len(trimmed) <= FAILURE_OUTPUT_MAX_CHARS:
        return trimmed
    return trimmed[-FAILURE_OUTPUT_MAX_CHARS:]


def _run_with_live_output(
    cmd: List[str],
    cwd: Optional[Path],
    env: Optional[dict],
) -> Tuple[int, str]:
    """Stream command output live while retaining a bounded failure excerpt."""
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )
    output_tail: Deque[str] = deque(maxlen=FAILURE_OUTPUT_MAX_LINES)
    if process.stdout is None:
        try:
            return process.wait(), ""
        except KeyboardInterrupt:
            _terminate_subprocess_tree(process)
            raise
    try:
        for line in process.stdout:
            print(line, end="")
            output_tail.append(line.rstrip("\n"))
        return process.wait(), "\n".join(output_tail)
    except KeyboardInterrupt:
        _terminate_subprocess_tree(process)
        raise
    finally:
        process.stdout.close()


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
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    dry_run: bool = False,
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
        returncode, output_tail = _run_with_live_output(cmd, cwd=cwd, env=env)
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


def build_env(args) -> dict:
    """Build env vars from common CLI flags (offline/cargo cache options)."""
    env = os.environ.copy()
    if getattr(args, "offline", False):
        env["CARGO_NET_OFFLINE"] = "true"
    if getattr(args, "cargo_home", None):
        env["CARGO_HOME"] = os.path.expanduser(args.cargo_home)
    if getattr(args, "cargo_target_dir", None):
        env["CARGO_TARGET_DIR"] = os.path.expanduser(args.cargo_target_dir)
    return env


def write_output(content: str, output_path: Optional[str]) -> None:
    """Write report output to a file, or print it to stdout."""
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        print(f"Report saved to: {path}")
    else:
        print(content)


def pipe_output(content: str, pipe_command: Optional[str], pipe_args: Optional[List[str]]) -> int:
    """Send report output to another command through stdin."""
    if not pipe_command:
        return 0
    cmd = [pipe_command] + (pipe_args or [])
    if not shutil.which(cmd[0]):
        print(f"Pipe command not found: {cmd[0]}")
        return 2
    result = subprocess.run(cmd, input=content, text=True)
    return result.returncode


def should_emit_output(args) -> bool:
    """Return True when the caller asked for formatted/output report text."""
    return args.format != "text" or bool(args.output) or bool(getattr(args, "pipe_command", None))


def confirm_or_abort(message: str, assume_yes: bool) -> None:
    """Ask for yes/no confirmation unless `--yes` was provided."""
    if assume_yes:
        return
    try:
        reply = input(f"{message} [y/N] ").strip().lower()
    except EOFError:
        print(f"{message} [y/N] <non-interactive input unavailable>")
        print("Aborted. Re-run with --yes for non-interactive usage.")
        raise SystemExit(1)
    if reply not in ("y", "yes"):
        print("Aborted.")
        raise SystemExit(1)


def find_latest_outcomes_file() -> Optional[Path]:
    """Find the newest mutation `outcomes.json` file under `src/mutants.out`."""
    output_dir = SRC_DIR / "mutants.out"
    primary = output_dir / "outcomes.json"
    if primary.exists():
        return primary
    candidates = list(output_dir.rglob("outcomes.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)
