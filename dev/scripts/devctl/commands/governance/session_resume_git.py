"""Git and guard-bundle helpers for session-resume packets."""

from __future__ import annotations

import subprocess
from pathlib import Path

_BUNDLE_BY_LANE = {
    "docs": "bundle.docs",
    "runtime": "bundle.runtime",
    "tooling": "bundle.tooling",
    "release": "bundle.release",
}


def resolve_guard_bundle(
    repo_root: Path,
    changed_paths: list[str] | None,
    *,
    head_sha: str = "",
    last_reviewed_sha: str = "",
) -> str:
    """Classify changed paths into the appropriate guard bundle name.

    Source precedence: (1) explicit ``changed_paths``, (2) live local
    worktree diffs, (3) commit-range fallback only when local diffs are
    empty and ``last_reviewed_sha != head_sha``. This ensures dirty local
    changes always take priority over older commit-range diffs.
    """
    if changed_paths is not None:
        paths = changed_paths
    else:
        paths = _git_changed_paths(repo_root)
        if not paths and last_reviewed_sha and head_sha and last_reviewed_sha != head_sha:
            paths = _git_commit_range_paths(repo_root, last_reviewed_sha, head_sha)
    if not paths:
        return ""
    try:
        from ..check.router_support import classify_lane

        result = classify_lane(paths, repo_root=repo_root)
        lane = str(result.get("lane", "")).strip()
        return _BUNDLE_BY_LANE.get(lane, "")
    except Exception:  # broad-except: allow reason=graceful degradation when router is unavailable fallback=return empty
        return ""


def current_head(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _git_changed_paths(repo_root: Path) -> list[str]:
    """Return changed file paths from unstaged and staged diffs."""
    try:
        for cmd in (["git", "diff", "--name-only", "HEAD"],
                    ["git", "diff", "--name-only", "--cached"]):
            out = subprocess.run(
                cmd,
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            ).stdout.strip()
            paths = [path for path in out.splitlines() if path.strip()]
            if paths:
                return paths
        return []
    except (OSError, subprocess.TimeoutExpired):
        return []


def _git_commit_range_paths(repo_root: Path, from_sha: str, to_sha: str) -> list[str]:
    """Return file paths changed between two commits."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{from_sha}..{to_sha}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return [path for path in result.stdout.strip().splitlines() if path.strip()]
    except Exception:  # broad-except: allow reason=git may fail on shallow clones or missing refs fallback=return empty
        return []
