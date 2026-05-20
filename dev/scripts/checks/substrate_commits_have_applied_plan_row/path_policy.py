"""Path policy helpers for substrate commit checks."""

from __future__ import annotations


def path_is_substrate(
    path: str,
    *,
    substrate_paths: tuple[str, ...],
    ignore_paths: tuple[str, ...],
) -> bool:
    normalized = path.strip().lstrip("./")
    if not normalized or path_matches_any(normalized, ignore_paths):
        return False
    return path_matches_any(normalized, substrate_paths)


def path_matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        normalized = pattern.strip().lstrip("./")
        if not normalized:
            continue
        if normalized.endswith("/"):
            if path.startswith(normalized):
                return True
            continue
        if path == normalized:
            return True
    return False
