"""Command-string rendering and pipe-output helpers."""

import shlex
import shutil
import subprocess

PIPE_OUTPUT_TIMEOUT_SECONDS = 120.0


def cmd_str(cmd: list[str]) -> str:
    """Render a command list as a printable string."""
    return shlex.join(cmd)


def pipe_output(content: str, pipe_command: str | None, pipe_args: list[str] | None) -> int:
    """Send report output to another command through stdin."""
    if not pipe_command:
        return 0
    cmd = [pipe_command] + (pipe_args or [])
    if not shutil.which(cmd[0]):
        print(f"Pipe command not found: {cmd[0]}")
        return 2
    try:
        result = subprocess.run(
            cmd,
            input=content,
            text=True,
            timeout=PIPE_OUTPUT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"Pipe command timed out after {PIPE_OUTPUT_TIMEOUT_SECONDS:.0f}s: {cmd_str(cmd)}")
        return 124
    except OSError as exc:
        print(f"Pipe command failed to start ({cmd_str(cmd)}): {exc}")
        return 127
    return result.returncode
