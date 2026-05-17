"""Dirty managed-projection status parsing for governed push receipts."""

from __future__ import annotations

from pathlib import Path

from ...runtime.vcs import run_git_capture


def dirty_managed_projection_paths(
    *,
    managed_paths: set[str],
    repo_root: Path,
) -> dict[str, object]:
    code, output, error = run_git_capture(
        ["status", "--porcelain", "--untracked-files=all"],
        repo_root=repo_root,
    )
    if code != 0:
        return {
            "ok": False,
            "reason": "git_status_failed",
            "error": error,
        }
    paths: set[str] = set()
    unmanaged: set[str] = set()
    for line in output.splitlines():
        if not line:
            continue
        raw_status, path = parse_porcelain_status_line(line)
        if "->" in path:
            path = path.split("->")[-1].strip()
        if not path:
            continue
        if path in managed_paths:
            paths.add(path)
            continue
        status = raw_status.strip()
        worktree_status = raw_status[1:2]
        if status == "??" or (worktree_status and worktree_status != " "):
            unmanaged.add(path)
    return {
        "ok": True,
        "reason": "dirty_paths_loaded",
        "dirty_paths": tuple(sorted(paths)),
        "unmanaged_paths": tuple(sorted(unmanaged)),
    }


def parse_porcelain_status_line(line: str) -> tuple[str, str]:
    """Parse a git-porcelain row after `run_git_capture` trims leading space."""
    if len(line) >= 3 and line[2:3] == " ":
        return line[:2], line[3:].strip()
    if len(line) >= 2 and line[1:2] == " ":
        return f" {line[:1]}", line[2:].strip()
    return line[:2], line[3:].strip()


__all__ = ["dirty_managed_projection_paths", "parse_porcelain_status_line"]
