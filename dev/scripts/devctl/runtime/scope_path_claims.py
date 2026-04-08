"""Shared path-claim parsing and matching helpers for typed startup/runtime state."""

from __future__ import annotations

import re
from collections.abc import Iterable

_PATH_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_./-]+\.(?:py|rs|md|json|ya?ml|toml|txt|tsx?|jsx?|sh))"
)


def extract_scope_paths(*texts: str) -> tuple[str, ...]:
    """Extract unique repo-relative file paths from freeform scope text."""
    scope_paths: list[str] = []
    for text in texts:
        for match in _PATH_RE.finditer(text):
            path = normalize_scope_path(match.group("path"))
            if path and path not in scope_paths:
                scope_paths.append(path)
    return tuple(scope_paths)


def normalize_scope_path(path: str) -> str:
    """Normalize one repo-relative scope path."""
    return path.strip().lstrip("./").replace("\\", "/")


def path_matches_scope_claim(path: str, scope_paths: Iterable[str]) -> bool:
    """Return True when *path* falls under one of the claimed scope paths."""
    normalized_path = normalize_scope_path(path)
    if not normalized_path:
        return False
    for raw_scope in scope_paths:
        scope = normalize_scope_path(raw_scope)
        if not scope:
            continue
        if normalized_path == scope or normalized_path.startswith(scope.rstrip("/") + "/"):
            return True
    return False


__all__ = ["extract_scope_paths", "normalize_scope_path", "path_matches_scope_claim"]
