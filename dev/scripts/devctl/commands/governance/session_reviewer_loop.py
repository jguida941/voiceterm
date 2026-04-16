"""Reviewer loop: delegates to the governed ensure-follow runtime.

Instead of spawning raw codex --full-auto passes, this wires into the
existing review-channel ensure --follow runtime which owns:
- Publisher heartbeat lifecycle
- Reviewer supervisor auto-restart
- Typed wake signals (pending packets, worktree drift, implementer state)
- Reviewer wake/relaunch via follow_controller

Per Codex rev_pkt_0791: the reviewer needs a durable runtime that
re-enters the next review cycle, not one-shot chat turns.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from ...config import get_repo_root


def run_reviewer_loop(
    *,
    repo_root: Path,
    interval: int = 30,
    headless: bool = False,
) -> int:
    """Start the governed reviewer runtime via ensure --follow.

    This delegates to ``review-channel --action ensure --follow`` which
    owns the full reviewer lifecycle: publisher heartbeat, supervisor
    auto-restart, typed wake signals, and reviewer conductor relaunch.

    The --follow flag keeps the runtime alive indefinitely. The
    --follow-inactivity-timeout-seconds 0 prevents timeout exits.
    """
    if not headless and not sys.stdin.isatty():
        print(
            "[session] ERROR: stdin is not a terminal. "
            "Use --headless or run in Terminal.app.",
            file=sys.stderr,
        )
        return 1

    print(f"[session] Starting governed reviewer runtime (interval={interval}s)")
    print(f"[session] Delegating to: review-channel --action ensure --follow")
    print(f"[session] Repo: {repo_root}")

    cmd = [
        sys.executable,
        "dev/scripts/devctl.py",
        "review-channel",
        "--action", "ensure",
        "--follow",
        "--follow-interval-seconds", str(interval),
        "--follow-inactivity-timeout-seconds", "0",
        "--terminal", "none",
        "--format", "json",
        "--execution-mode", "markdown-bridge",
    ]

    # --loop implies continuous automated operation, which requires
    # remote_control interaction mode for the wake controller to
    # actually relaunch the reviewer (rev_pkt_0794).
    import os
    env = {**os.environ, "DEVCTL_OPERATOR_INTERACTION_MODE": "remote_control"}

    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\n[session] Reviewer runtime stopped by user.")
        return 0
    except FileNotFoundError:
        print("[session] ERROR: python3 not found", file=sys.stderr)
        return 127
