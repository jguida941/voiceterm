"""Shared git range helpers for guard commands."""

from __future__ import annotations

from pathlib import Path
import subprocess


def git_commit_range(
    *,
    repo_root: Path,
    base_ref: str,
    head_ref: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return commits in ``base_ref..head_ref`` plus non-fatal warnings."""
    if not git_ref_exists(repo_root, base_ref):
        return (), (f"base_ref_unavailable:{base_ref}",)
    result = subprocess.run(
        ("git", "rev-list", "--reverse", f"{base_ref}..{head_ref}"),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        warning = result.stderr.strip() or result.stdout.strip() or "git_rev_list_failed"
        return (), (warning,)
    commits = tuple(line.strip() for line in result.stdout.splitlines() if line.strip())
    return commits, ()


def git_ref_exists(repo_root: Path, ref: str) -> bool:
    """Return whether ``ref`` resolves in ``repo_root``."""
    result = subprocess.run(
        ("git", "rev-parse", "--verify", ref),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0
