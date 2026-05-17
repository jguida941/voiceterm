"""Git ref and unpublished-commit helpers for orphan inventory scans."""

from __future__ import annotations

from pathlib import Path

from .vcs import run_git_capture
from .worktree_orphan_inventory_git_common import git_output

MAX_UNPUBLISHED_COMMITS = 50


def unpublished_commits(path: Path, *, branch: str) -> tuple[str, ...]:
    """Return commits in HEAD that have not reached the configured upstream."""
    rev_range = unpublished_rev_range(
        path,
        branch=branch,
        upstream=upstream_ref(path),
    )
    if not rev_range:
        return ()

    return rev_list_commits(path, rev_range)


def upstream_ref(path: Path) -> str:
    return git_output(
        path,
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
    )


def unpublished_rev_range(path: Path, *, branch: str, upstream: str) -> str:
    if upstream:
        return f"{upstream}..HEAD"
    if branch and branch_exists(path, f"origin/{branch}"):
        return f"origin/{branch}..HEAD"
    return ""


def rev_list_commits(path: Path, rev_range: str) -> tuple[str, ...]:
    code, output, _ = run_git_capture(
        ["rev-list", f"--max-count={MAX_UNPUBLISHED_COMMITS}", rev_range],
        repo_root=path,
    )
    if code != 0 or not output:
        return ()

    return tuple(line.strip() for line in output.splitlines() if line.strip())


def branch_exists(repo_root: Path, branch: str) -> bool:
    """Return true if a local or remote branch ref exists."""
    if not branch:
        return False

    code, _, _ = run_git_capture(
        ["rev-parse", "--verify", "--quiet", branch],
        repo_root=repo_root,
    )
    if code == 0:
        return True

    code, _, _ = run_git_capture(
        ["rev-parse", "--verify", "--quiet", f"refs/remotes/{branch}"],
        repo_root=repo_root,
    )
    return code == 0


__all__ = ["branch_exists", "unpublished_commits"]
