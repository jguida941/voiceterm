"""Same-parent checkout candidate discovery for orphan inventory scans."""

from __future__ import annotations

from pathlib import Path

MAX_SIBLING_CANDIDATES = 96


def same_parent_candidates(parent: Path, repo_name: str) -> tuple[Path, ...]:
    """Return bounded same-parent directories whose names match this repo."""
    try:
        candidates = sorted(
            (
                item
                for item in parent.iterdir()
                if item.is_dir()
                and item.name != repo_name
                and item.name.startswith(repo_name)
            ),
            key=lambda item: item.name,
        )
    except OSError:
        return ()

    return tuple(candidates[:MAX_SIBLING_CANDIDATES])


def looks_like_git_checkout(path: Path) -> bool:
    return (path / ".git").exists()


__all__ = ["looks_like_git_checkout", "same_parent_candidates"]
