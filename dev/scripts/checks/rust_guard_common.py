"""Shared helpers for Rust guard scripts."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(
    repo_root: Path,
    args: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run git with a stable error contract used by guard scripts."""
    result = subprocess.run(
        args,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip() or "git command failed")
    return result


def validate_ref(run_git_fn, ref: str) -> None:
    """Ensure a ref resolves before commit-range checks run."""
    run_git_fn(["git", "rev-parse", "--verify", ref], check=True)


def is_test_path(path: Path) -> bool:
    """Return True when a Rust path is test-only."""
    normalized = f"/{path.as_posix()}/"
    name = path.name
    return (
        "/tests/" in normalized
        or name == "tests.rs"
        or name.endswith("_test.rs")
        or name.endswith("_tests.rs")
    )


def read_text_from_ref(run_git_fn, path: Path, ref: str) -> str | None:
    """Read repo-relative file text from a git ref."""
    spec = f"{ref}:{path.as_posix()}"
    result = run_git_fn(["git", "show", spec], check=False)
    if result.returncode == 0:
        return result.stdout

    stderr = result.stderr.strip().lower()
    missing_markers = ("does not exist in", "exists on disk, but not in", "fatal: path")
    if any(marker in stderr for marker in missing_markers):
        return None
    raise RuntimeError(result.stderr.strip() or f"failed to read {spec}")


def read_text_from_worktree(repo_root: Path, path: Path) -> str | None:
    """Read repo-relative file text from the worktree."""
    absolute = repo_root / path
    if not absolute.exists():
        return None
    return absolute.read_text(encoding="utf-8", errors="replace")
