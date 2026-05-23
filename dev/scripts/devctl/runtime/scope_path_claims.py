"""Shared path-claim parsing and matching helpers for typed startup/runtime state."""

from __future__ import annotations

import re
from collections.abc import Iterable

_PATH_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_./-]+\.(?:py|rs|md|jsonl?|ya?ml|toml|txt|tsx?|jsx?|sh))"
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


def paths_overlap(left: str, right: str) -> bool:
    """Return True when two scope paths overlap by prefix containment.

    Two paths overlap when they are equal after trailing-slash normalization
    or one is a strict directory ancestor of the other. Empty inputs never
    overlap. Callers may pass already-normalized values; this helper is
    idempotent under repeated ``rstrip("/")``.
    """
    if not left or not right:
        return False
    left_n = left.rstrip("/")
    right_n = right.rstrip("/")
    if left_n == right_n:
        return True
    return left_n.startswith(f"{right_n}/") or right_n.startswith(f"{left_n}/")


__all__ = [
    "extract_scope_paths",
    "normalize_scope_path",
    "path_matches_scope_claim",
    "paths_overlap",
]
