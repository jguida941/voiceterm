"""Managed projection path helpers for governed VCS staging."""

from __future__ import annotations

from typing import Any


def include_managed_projection_paths(
    *,
    selected_paths: list[str],
    startup_context: Any,
) -> tuple[list[str], list[str]]:
    """Expand explicit stage scope with startup-classified projection drift."""
    if not selected_paths:
        return selected_paths, []
    selected = list(selected_paths)
    seen = set(selected)
    included: list[str] = []
    for path in managed_projection_dirty_paths(startup_context):
        if path in seen:
            continue
        selected.append(path)
        seen.add(path)
        included.append(path)
    if not included:
        return selected, []
    return selected, [
        "managed_projection_paths_auto_included="
        + ",".join(sorted(included))
    ]


def managed_projection_dirty_paths(startup_context: Any) -> tuple[str, ...]:
    governance = _field(startup_context, "governance")
    push = _field(governance, "push_enforcement")
    raw = _field(push, "managed_projection_dirty_paths")
    if not isinstance(raw, (list, tuple)):
        return ()
    paths: list[str] = []
    seen: set[str] = set()
    for item in raw:
        path = str(item or "").strip()
        if not path or path in seen:
            continue
        paths.append(path)
        seen.add(path)
    return tuple(paths)


def _field(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


__all__ = [
    "include_managed_projection_paths",
    "managed_projection_dirty_paths",
]
