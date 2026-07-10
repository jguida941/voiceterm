"""Git and path helpers for publication-sync drift detection."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ..common import display_path


def run_git(repo_root: Path, *args: str) -> str:
    """Run one git command and return trimmed stdout."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ValueError(f"unable to run git {' '.join(args)}: {exc}") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or "unknown git failure"
        raise ValueError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def resolve_git_ref(repo_root: Path, ref: str) -> str:
    """Resolve one git ref to a concrete commit hash."""
    normalized = str(ref).strip()
    if not normalized:
        raise ValueError("source_ref is missing")
    return run_git(repo_root, "rev-parse", f"{normalized}^{{commit}}")


def list_changed_paths(repo_root: Path, source_ref: str, head_ref: str) -> list[str]:
    """List changed tracked paths between two resolved commit hashes."""
    if source_ref == head_ref:
        return []
    output = run_git(
        repo_root,
        "diff",
        "--name-only",
        "--find-renames",
        f"{source_ref}..{head_ref}",
        "--",
    )
    return sorted(path.strip() for path in output.splitlines() if path.strip())


def list_dirty_paths(repo_root: Path) -> list[str]:
    """List paths changed or untracked in the working tree relative to HEAD.

    Combines tracked dirty files (staged + unstaged via ``git diff HEAD``)
    with untracked files (via ``git ls-files --others --exclude-standard``)
    so that new files under watched directories are visible to drift detection.
    """
    paths: set[str] = set()
    try:
        diff_output = run_git(repo_root, "diff", "--name-only", "HEAD", "--")
        paths.update(p.strip() for p in diff_output.splitlines() if p.strip())
    except ValueError:
        pass
    try:
        untracked_output = run_git(
            repo_root, "ls-files", "--others", "--exclude-standard",
        )
        paths.update(p.strip() for p in untracked_output.splitlines() if p.strip())
    except ValueError:
        pass
    return sorted(paths)


def normalize_watched_path(raw: Any) -> str:
    """Normalize a watched path for consistent matching."""
    value = str(raw).strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value.rstrip("/")


def path_matches_watch(path: str, watched_path: str) -> bool:
    """Check whether a file path falls under a watched directory or matches exactly."""
    normalized_path = path.strip().replace("\\", "/").rstrip("/")
    normalized_watch = normalize_watched_path(watched_path)
    return bool(normalized_watch) and (
        normalized_path == normalized_watch
        or normalized_path.startswith(f"{normalized_watch}/")
    )
