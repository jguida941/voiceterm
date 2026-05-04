"""Process-tree teardown helper for command-runner subprocesses."""

from __future__ import annotations

import os
import signal
import subprocess

INTERRUPT_KILL_GRACE_SECONDS = 3.0


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


__all__ = ["INTERRUPT_KILL_GRACE_SECONDS", "_terminate_subprocess_tree"]
