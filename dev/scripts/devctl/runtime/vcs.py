"""Shared git/vcs helpers used by repo-owned command surfaces."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

from ..config import REPO_ROOT


def run_git_capture(
    args: Sequence[str],
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[int, str, str]:
    """Run a git command and return ``(returncode, stdout, stderr)``."""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return (
        completed.returncode,
        (completed.stdout or "").strip(),
        (completed.stderr or "").strip(),
    )


def remote_exists(remote: str, *, repo_root: Path = REPO_ROOT) -> bool:
    """Return ``True`` when a named remote is configured locally."""
    code, _, _ = run_git_capture(["remote", "get-url", remote], repo_root=repo_root)
    return code == 0


def branch_exists(branch: str, *, repo_root: Path = REPO_ROOT) -> bool:
    """Return ``True`` when a local branch exists."""
    code, _, _ = run_git_capture(
        ["rev-parse", "--verify", "--quiet", branch],
        repo_root=repo_root,
    )
    return code == 0


def remote_branch_exists(
    remote: str,
    branch: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> bool:
    """Return ``True`` when ``refs/remotes/<remote>/<branch>`` exists."""
    code, _, _ = run_git_capture(
        ["show-ref", "--verify", "--quiet", f"refs/remotes/{remote}/{branch}"],
        repo_root=repo_root,
    )
    return code == 0


def branch_divergence(
    remote: str,
    branch: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, int | str | None]:
    """Return ahead/behind counts for ``branch`` against ``remote/branch``."""
    code, output, error = run_git_capture(
        ["rev-list", "--left-right", "--count", f"{remote}/{branch}...{branch}"],
        repo_root=repo_root,
    )
    if code != 0:
        message = error or output or f"git rev-list exited with code {code}"
        return {"behind": None, "ahead": None, "error": message}

    parts = output.split()
    if len(parts) != 2:
        return {
            "behind": None,
            "ahead": None,
            "error": f"Unexpected divergence output: {output!r}",
        }

    try:
        behind = int(parts[0])
        ahead = int(parts[1])
    except ValueError:
        return {
            "behind": None,
            "ahead": None,
            "error": f"Unable to parse divergence output: {output!r}",
        }
    return {"behind": behind, "ahead": ahead, "error": None}
