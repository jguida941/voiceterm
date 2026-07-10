"""Git status parsing for worktree-orphan inventory scans."""

from __future__ import annotations

from pathlib import Path

from .vcs import run_git_capture

PORCELAIN_STATUS_WIDTH = 2
PORCELAIN_PATH_START = 3
STRIPPED_STATUS_PATH_START = 2


def status_paths(path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return tracked-dirty and untracked paths from git porcelain output."""
    code, output, _ = run_git_capture(
        ["status", "--porcelain=v1", "--untracked-files=all"],
        repo_root=path,
    )
    if code != 0 or not output:
        return (), ()

    dirty: list[str] = []
    untracked: list[str] = []
    for line in output.splitlines():
        parsed_path = status_path(line)
        if not parsed_path:
            continue
        if line.startswith("??"):
            untracked.append(parsed_path)
        else:
            dirty.append(parsed_path)

    return tuple(dirty), tuple(untracked)


def status_path(line: str) -> str:
    """Extract a path from porcelain output after run_git_capture stripping."""
    if len(line) < PORCELAIN_PATH_START:
        return ""

    if line.startswith("?? "):
        path = line[PORCELAIN_PATH_START:]
    elif len(line) >= 4 and line[PORCELAIN_STATUS_WIDTH] == " ":
        path = line[PORCELAIN_PATH_START:]
    elif len(line) >= 3 and line[1] == " ":
        path = line[STRIPPED_STATUS_PATH_START:]
    else:
        parts = line.split(maxsplit=1)
        path = parts[1] if len(parts) == 2 else ""

    return path.split(" -> ", 1)[1] if " -> " in path else path


__all__ = ["status_paths"]
