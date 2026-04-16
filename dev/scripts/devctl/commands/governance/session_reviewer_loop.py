"""Reviewer loop: continuous Codex reviewer with governed lifecycle.

Replaces dev/scripts/reviewer_loop.sh with a proper devctl-integrated
loop that writes heartbeats, checks inbox via typed state, and
relaunches Codex after each pass. Uses the existing review-channel
infrastructure instead of raw shell commands.
"""

from __future__ import annotations

import json
import signal
import subprocess
import sys
import time
from pathlib import Path

from ...config import get_repo_root


REVIEWER_PROMPT = (
    "You are the Codex REVIEWER. "
    "Step 1: Read inbox: python3 dev/scripts/devctl.py review-channel "
    "--action inbox --target codex --status pending --terminal none "
    "--format md --execution-mode markdown-bridge. "
    "Step 2: Review all worktree changes: git diff --stat, git diff --cached --stat, "
    "then read each changed file. "
    "Step 3: Post findings via: python3 dev/scripts/devctl.py review-channel "
    "--action post --from-agent codex --to-agent claude --kind finding "
    "--summary YOUR_SUMMARY --body YOUR_DETAILS --terminal none "
    "--format json --execution-mode markdown-bridge. "
    "Step 4: Post a summary instruction when done."
)


def run_reviewer_loop(
    *,
    repo_root: Path,
    interval: int = 30,
    headless: bool = False,
) -> int:
    """Run the continuous reviewer loop. Returns exit code on clean shutdown."""
    if not headless and not sys.stdin.isatty():
        print(
            "[session] ERROR: stdin is not a terminal. "
            "Codex requires a TTY. Use --headless or run in Terminal.app.",
            file=sys.stderr,
        )
        return 1

    shutdown_requested = False

    def _handle_signal(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True
        print(f"\n[session] Received signal {signum}, shutting down after current pass.")

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print(f"[session] Starting reviewer loop (interval={interval}s, headless={headless})")
    print(f"[session] Repo: {repo_root}")

    round_num = 0
    while not shutdown_requested:
        round_num += 1
        print(f"\n[session] === Round {round_num} ===")

        pending = _check_pending_packets(repo_root)
        dirty = _check_worktree_dirty(repo_root)
        print(f"[session] Pending packets: {pending}, Dirty files: {dirty}")

        if pending > 0 or dirty > 0:
            print("[session] Launching Codex reviewer pass...")
            exit_code = _launch_codex_pass(repo_root, headless=headless)
            if exit_code != 0:
                print(f"[session] WARNING: Codex exited with code {exit_code}")
                _post_failure_packet(repo_root, exit_code, round_num)
            else:
                print("[session] Codex pass completed successfully.")
        else:
            print(f"[session] Nothing to review. Waiting {interval}s...")

        if not shutdown_requested:
            time.sleep(interval)

    print("[session] Reviewer loop shut down cleanly.")
    return 0


def _check_pending_packets(repo_root: Path) -> int:
    """Check how many packets are pending for the codex agent."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "dev/scripts/devctl.py",
                "review-channel", "--action", "inbox",
                "--target", "codex", "--status", "pending",
                "--terminal", "none", "--format", "json",
                "--execution-mode", "markdown-bridge",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"[session] WARNING: inbox check failed (exit {result.returncode})")
            return -1
        data = json.loads(result.stdout)
        return int(data.get("queue", {}).get("pending_codex", 0))
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"[session] WARNING: inbox check error: {exc}")
        return -1


def _check_worktree_dirty(repo_root: Path) -> int:
    """Count dirty files: unstaged + staged + untracked."""
    total = 0
    for cmd in (
        ["git", "diff", "--stat"],
        ["git", "diff", "--cached", "--stat"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        try:
            result = subprocess.run(
                cmd, cwd=str(repo_root),
                capture_output=True, text=True, timeout=10,
            )
            total += len(result.stdout.strip().splitlines())
        except (subprocess.TimeoutExpired, OSError):
            pass
    return total


def _launch_codex_pass(repo_root: Path, *, headless: bool = False) -> int:
    """Launch one Codex --full-auto reviewer pass."""
    cmd = ["codex", "--full-auto", REVIEWER_PROMPT]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            timeout=600,
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        print("[session] WARNING: Codex pass timed out after 600s")
        return 124
    except FileNotFoundError:
        print("[session] ERROR: codex not found in PATH")
        return 127
    except OSError as exc:
        print(f"[session] ERROR: failed to launch codex: {exc}")
        return 1


def _post_failure_packet(repo_root: Path, exit_code: int, round_num: int) -> None:
    """Post a failure finding to Claude when a Codex pass fails."""
    try:
        subprocess.run(
            [
                sys.executable,
                "dev/scripts/devctl.py",
                "review-channel", "--action", "post",
                "--from-agent", "codex",
                "--to-agent", "claude",
                "--kind", "finding",
                "--summary", f"Codex reviewer pass failed (round {round_num}, exit {exit_code})",
                "--body", (
                    f"The Codex reviewer pass exited with code {exit_code} in round {round_num}. "
                    "This may indicate a sandbox escalation, TTY issue, or runtime error. "
                    "Check the Codex session log at ~/.codex/sessions/ for details."
                ),
                "--terminal", "none",
                "--format", "json",
                "--execution-mode", "markdown-bridge",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass
