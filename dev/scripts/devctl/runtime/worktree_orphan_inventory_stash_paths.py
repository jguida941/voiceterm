"""Stash file/section readers for worktree-orphan inventory scans."""

from __future__ import annotations

from pathlib import Path

from .vcs import run_git_capture


def stash_sections(repo_root: Path, stash_ref: str) -> tuple[str, ...]:
    code, output, _ = run_git_capture(
        ["rev-list", "--parents", "-n", "1", stash_ref],
        repo_root=repo_root,
    )
    if code != 0 or not output:
        return ("working_tree",)

    parts = output.split()
    sections = ["working_tree"]
    if len(parts) >= 3:
        sections.append("index")
    if len(parts) >= 4:
        sections.append("untracked")

    return tuple(sections)


def stash_file_paths(
    repo_root: Path,
    stash_ref: str,
    *,
    sections: tuple[str, ...],
) -> tuple[str, ...]:
    files = list(stash_show_paths(repo_root, stash_ref))
    if "untracked" in sections:
        files.extend(stash_untracked_paths(repo_root, stash_ref))

    return tuple(dict.fromkeys(files))


def stash_show_paths(repo_root: Path, stash_ref: str) -> tuple[str, ...]:
    code, output, _ = run_git_capture(
        ["stash", "show", "--name-only", stash_ref],
        repo_root=repo_root,
    )
    if code != 0 or not output:
        return ()

    return tuple(line.strip() for line in output.splitlines() if line.strip())


def stash_untracked_paths(repo_root: Path, stash_ref: str) -> tuple[str, ...]:
    code, output, _ = run_git_capture(
        ["diff", "--name-only", f"{stash_ref}^1", f"{stash_ref}^3"],
        repo_root=repo_root,
    )
    if code != 0 or not output:
        return ()

    return tuple(line.strip() for line in output.splitlines() if line.strip())


__all__ = ["stash_file_paths", "stash_sections"]
