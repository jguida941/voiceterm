"""Hybrid reviewer loop: ensure-follow heartbeats + direct Codex launches.

Runs ensure --follow as a short tick for heartbeats/supervisor state,
then checks for pending packets or dirty worktree. When work exists
and no Codex process is alive, launches ``codex --full-auto`` directly,
waits for it to finish, and loops back.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_reviewer_loop(
    *,
    repo_root: Path,
    interval: int = 30,
    headless: bool = False,
) -> int:
    """Run the hybrid reviewer loop: heartbeat ticks + Codex launches."""
    if not headless and not sys.stdin.isatty():
        print(
            "[session] ERROR: stdin is not a terminal. "
            "Use --headless or run in Terminal.app.",
            file=sys.stderr,
        )
        return 1

    print(f"[session] Starting hybrid reviewer loop (tick={interval}s)")
    print(f"[session] Repo: {repo_root}")

    try:
        while True:
            _run_ensure_tick(repo_root, interval)
            if _has_pending_work(repo_root) and not _codex_is_running():
                _launch_codex_review(repo_root)
    except KeyboardInterrupt:
        print("\n[session] Reviewer loop stopped by user.")
        return 0


def _run_ensure_tick(repo_root: Path, interval: int) -> None:
    """Run one ensure --follow tick as a subprocess with a short timeout."""
    cmd = [
        sys.executable,
        "dev/scripts/devctl.py",
        "review-channel",
        "--action", "ensure",
        "--follow",
        "--follow-interval-seconds", str(interval),
        "--follow-inactivity-timeout-seconds", str(interval),
        "--terminal", "none",
        "--format", "json",
        "--execution-mode", "markdown-bridge",
    ]
    env = {**os.environ, "DEVCTL_OPERATOR_INTERACTION_MODE": "remote_control"}
    try:
        subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
            timeout=interval + 15,
        )
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        print("[session] WARNING: python3 not found for ensure tick",
              file=sys.stderr)


def _has_pending_work(repo_root: Path) -> bool:
    """Return True when there are pending packets or uncommitted changes."""
    try:
        from ...review_channel.pending_packet_storage import (
            load_pending_packets,
        )
        if load_pending_packets(repo_root):
            return True
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.stdout.strip():
            return True
    except Exception:
        pass
    return False


def _codex_is_running() -> bool:
    """Check whether any codex process is currently alive."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "codex"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _launch_codex_review(repo_root: Path) -> None:
    """Launch codex --full-auto for one review pass, wait for it to finish."""
    codex_bin = shutil.which("codex")
    if codex_bin is None:
        print("[session] WARNING: codex not found in PATH", file=sys.stderr)
        return

    prompt = (
        f"cd {repo_root} && "
        "python3 dev/scripts/devctl.py session-resume "
        "--role reviewer --format bootstrap | head -80\n\n"
        "You are the reviewer. Read the bootstrap output above, then:\n"
        "1. Run: python3 dev/scripts/devctl.py review-channel "
        "--action inbox --status pending --format json\n"
        "2. Review each pending packet and the current diff\n"
        "3. Post findings via: python3 dev/scripts/devctl.py "
        "review-channel --action reviewer-checkpoint "
        "--reviewer-mode active_dual_agent "
        "--reason review-pass --terminal none --format md\n"
        "4. Exit when done."
    )

    cmd = [
        codex_bin,
        "-C", str(repo_root),
        "--full-auto",
        "-q", prompt,
    ]
    print(f"[session] Launching Codex review pass...")
    try:
        result = subprocess.run(cmd, cwd=str(repo_root), timeout=300)
        print(f"[session] Codex exited with code {result.returncode}")
    except subprocess.TimeoutExpired:
        print("[session] Codex review timed out after 5 minutes")
    except Exception as exc:
        print(f"[session] Codex launch failed: {exc}", file=sys.stderr)
