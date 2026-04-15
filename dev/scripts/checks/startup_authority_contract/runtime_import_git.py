"""Git/index access helpers for startup-authority import atomicity checks."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _read_committed_file(
    repo_root: Path,
    relative: Path,
) -> tuple[str | None, str | None]:
    """Read a file's content from HEAD (the committed tree), not the working tree."""
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{relative.as_posix()}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, (
            f"{relative.as_posix()}: unable to read committed importer source ({exc})"
        )
    if result.returncode != 0:
        stderr = (
            str(getattr(result, "stderr", "") or "").strip()
            or "git show HEAD:<path> failed"
        )
        return None, (
            f"{relative.as_posix()}: unable to read committed importer source ({stderr})"
        )
    return result.stdout, None


def _list_staged_python_paths(repo_root: Path) -> tuple[set[str], str | None]:
    """Return Python paths present in the git index."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--", "*.py"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return set(), f"git index unavailable for import atomicity check ({exc})"
    if result.returncode != 0:
        stderr = str(getattr(result, "stderr", "") or "").strip() or "git ls-files failed"
        return set(), f"git index unavailable for import atomicity check ({stderr})"
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().endswith(".py")
    }, None


def _list_local_python_paths(repo_root: Path) -> tuple[set[str], str | None]:
    """Return changed or untracked Python paths visible in the local worktree."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", "*.py"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return set(), f"git worktree unavailable for import atomicity check ({exc})"
    if result.returncode != 0:
        stderr = (
            str(getattr(result, "stderr", "") or "").strip()
            or "git status --porcelain failed"
        )
        return set(), f"git worktree unavailable for import atomicity check ({stderr})"
    paths: set[str] = set()
    for line in result.stdout.splitlines():
        relative = _porcelain_relative_path(line)
        if relative and relative.endswith(".py"):
            paths.add(relative)
    return paths, None


def _list_committed_python_paths(repo_root: Path) -> tuple[set[str], str | None]:
    """Return Python paths in the committed tree (HEAD), not the staging area."""
    try:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return set(), f"git HEAD tree unavailable for import/index atomicity check ({exc})"
    if result.returncode != 0:
        stderr = str(getattr(result, "stderr", "") or "").strip() or "git ls-tree HEAD failed"
        if _head_missing(stderr):
            return set(), None
        return set(), f"git HEAD tree unavailable for import/index atomicity check ({stderr})"
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().endswith(".py")
    }, None


def _head_missing(stderr: str) -> bool:
    text = stderr.lower()
    return (
        "not a valid object name head" in text
        or "ambiguous argument 'head'" in text
        or "bad revision 'head'" in text
    )


def _porcelain_relative_path(line: str) -> str:
    text = str(line or "").rstrip()
    if len(text) < 4:
        return ""
    path_text = text[3:].strip()
    if " -> " in path_text:
        path_text = path_text.split(" -> ", 1)[1].strip()
    return path_text
