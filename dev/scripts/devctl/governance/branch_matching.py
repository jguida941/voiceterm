"""Branch-resolution helpers for branch-aware governance checks."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import REPO_ROOT


def _git_capture_lines(
    command: list[str],
    *,
    repo_root: Path = REPO_ROOT,
) -> list[str]:
    """Return stripped stdout lines for a git query or an empty list on failure."""
    try:
        output = subprocess.check_output(
            command,
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def branch_matches_named_branch(candidate: str, branch_name: str) -> bool:
    """Return True when a local or remote branch candidate names `branch_name`."""
    text = str(candidate or "").strip()
    if not text:
        return False
    normalized = text.removeprefix("remotes/")
    return normalized == branch_name or normalized.endswith(f"/{branch_name}")


def head_matches_branch(
    head_ref: str,
    branch_name: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> bool:
    """Return True when the current head resolves to `branch_name`."""
    if branch_matches_named_branch(head_ref, branch_name):
        return True

    current_branch = _git_capture_lines(
        ["git", "branch", "--show-current"],
        repo_root=repo_root,
    )
    if current_branch and branch_matches_named_branch(current_branch[0], branch_name):
        return True

    branch_name_lines = _git_capture_lines(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        repo_root=repo_root,
    )
    if branch_name_lines and branch_matches_named_branch(
        branch_name_lines[0],
        branch_name,
    ):
        return True

    reference = str(head_ref or "").strip() or "HEAD"
    branch_candidates = _git_capture_lines(
        [
            "git",
            "branch",
            "--all",
            "--contains",
            reference,
            "--format",
            "%(refname:short)",
        ],
        repo_root=repo_root,
    )
    return any(
        branch_matches_named_branch(candidate, branch_name)
        for candidate in branch_candidates
    )


def head_matches_release_branch(
    head_ref: str,
    release_branch: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> bool:
    """Return True when the current head resolves to the configured release branch."""
    return head_matches_branch(
        head_ref,
        release_branch,
        repo_root=repo_root,
    )
