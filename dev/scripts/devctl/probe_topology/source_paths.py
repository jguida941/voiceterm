"""Path and source-file discovery helpers for probe topology."""

from __future__ import annotations

from pathlib import Path

from ..config import get_repo_root

SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "target",
    "venv",
}
SKIP_PREFIXES: tuple[tuple[str, ...], ...] = (
    (".claude", "worktrees"),
    ("dev", "repo_example_temp"),
)


def repo_relative(path: Path) -> str:
    return path.relative_to(repo_root()).as_posix()


def repo_root() -> Path:
    """Return the active repo root for topology scans."""
    return get_repo_root()


def iter_source_files() -> dict[str, list[Path]]:
    buckets: dict[str, list[Path]] = {"python": [], "rust": []}
    current_repo_root = repo_root()
    for path in current_repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(current_repo_root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        if _has_skip_prefix(rel_parts):
            continue
        if path.suffix == ".py":
            buckets["python"].append(path)
        elif path.suffix == ".rs":
            buckets["rust"].append(path)
    return buckets


def _has_skip_prefix(rel_parts: tuple[str, ...]) -> bool:
    """Return whether a path lives under a path-specific excluded prefix."""
    for prefix in SKIP_PREFIXES:
        if rel_parts[: len(prefix)] == prefix:
            return True
    return False
