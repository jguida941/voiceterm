"""Hybrid reviewer loop: ensure-follow heartbeats + direct Codex launches.

Runs ensure --follow as a short tick for heartbeats/supervisor state,
then checks for pending packets or dirty worktree. When work exists
and no Codex process is alive, launches a bounded ``codex exec`` review
pass with the current CLI approval/sandbox flags, waits for it to finish,
and loops back.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from ...review_channel.collaboration_provider import reviewer_provider_from_review_state
from ...review_channel.pending_packet_storage import load_pending_reviewer_packets
from ...runtime.review_state_locator import load_current_review_state


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
            if _has_pending_work(repo_root) and not _codex_is_running(repo_root):
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
            check=False,
            timeout=interval + 15,
        )
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        print("[session] WARNING: python3 not found for ensure tick",
              file=sys.stderr)


def _has_pending_work(repo_root: Path) -> bool:
    """Return True when reviewer-targeted packets or relevant uncommitted changes exist."""
    try:
        review_state = load_current_review_state(
            repo_root,
            prefer_cached_projection=False,
        )
        reviewer_agent = reviewer_provider_from_review_state(review_state)
        if load_pending_reviewer_packets(repo_root, reviewer_agent=reviewer_agent):
            return True
    except Exception:
        pass
    if _has_reviewer_relevant_changes(repo_root):
        return True
    return False


# Paths that are projection artifacts or bridge drift, not reviewer-actionable changes.
_WORKTREE_NOISE_PREFIXES: tuple[str, ...] = (
    "bridge.md",
    "dev/reports/review_channel/",
    ".voiceterm/memory/",
)


def _has_reviewer_relevant_changes(repo_root: Path) -> bool:
    """Return True only when the dirty worktree has changes outside projection noise."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except Exception:
        return False
    for line in result.stdout.splitlines():
        # porcelain format: "XY <path>" -- path starts at column 3
        path = line[3:].strip().strip('"')
        if not any(path.startswith(prefix) for prefix in _WORKTREE_NOISE_PREFIXES):
            return True
    return False


def _codex_is_running(repo_root: Path) -> bool:
    """Check whether a Codex session is live for THIS repo, not globally."""
    try:
        from ...repo_packs import active_path_config
        from ...review_channel.session_probe import active_conductor_providers

        config = active_path_config()
        status_dir = repo_root / config.review_status_dir_rel
        providers = active_conductor_providers(session_output_root=status_dir)
        return "codex" in providers
    except Exception:
        pass
    # Fallback: narrow pgrep to codex processes whose cwd is this repo
    return _pgrep_codex_for_repo(repo_root)


def _pgrep_codex_for_repo(repo_root: Path) -> bool:
    """Fallback process check scoped to this repo's directory."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"codex.*{repo_root}"],
            capture_output=True,
            check=False,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _launch_codex_review(repo_root: Path) -> None:
    """Launch one bounded Codex review pass and wait for it to finish."""
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
        "--ask-for-approval", "on-request",
        "--sandbox", "workspace-write",
        "exec",
        prompt,
    ]
    print(f"[session] Launching Codex review pass...")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            check=False,
            timeout=300,
        )
        print(f"[session] Codex exited with code {result.returncode}")
    except subprocess.TimeoutExpired:
        print("[session] Codex review timed out after 5 minutes")
    except Exception as exc:
        print(f"[session] Codex launch failed: {exc}", file=sys.stderr)
