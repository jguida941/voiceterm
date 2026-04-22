"""Git stash inventory for worktree-orphan reports."""

from __future__ import annotations

from pathlib import Path

from .vcs import run_git_capture
from .worktree_orphan_inventory_stash_paths import stash_file_paths, stash_sections
from .worktree_orphan_inventory_stash_source import (
    build_stash_source,
    stash_entry_from_line,
)
from .worktree_orphan_snapshot import OrphanSource


def scan_stashes(repo_root: Path) -> tuple[tuple[OrphanSource, ...], tuple[str, ...]]:
    """Return stash-orphan sources plus non-fatal warnings."""
    code, output, stderr = run_git_capture(
        ["stash", "list", "--format=%gd%x1f%H%x1f%s"],
        repo_root=repo_root,
    )
    if code != 0:
        return (), (stderr or output or "git stash list failed",)

    return stash_sources_from_output(repo_root, output), ()


def stash_sources_from_output(repo_root: Path, output: str) -> tuple[OrphanSource, ...]:
    sources = []
    for index, line in enumerate(output.splitlines()):
        source = stash_source_from_line(repo_root, index=index, line=line)
        if source is not None:
            sources.append(source)

    return tuple(sources)


def stash_source_from_line(
    repo_root: Path,
    *,
    index: int,
    line: str,
) -> OrphanSource | None:
    entry = stash_entry_from_line(line)
    if entry is None:
        return None

    sections = stash_sections(repo_root, entry.stash_ref)
    files = stash_file_paths(repo_root, entry.stash_ref, sections=sections)

    return build_stash_source(
        index=index,
        entry=entry,
        sections=sections,
        files=files,
    )


__all__ = ["scan_stashes"]
