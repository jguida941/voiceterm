"""Shared scalar coercion helpers for agent-loop decisions."""

from __future__ import annotations

from .value_coercion import coerce_text as _text


def string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(_text(item) for item in value if _text(item))


def truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return _text(value).lower() in {"1", "true", "yes", "y", "on", "live", "attached"}


__all__ = ["string_tuple", "truthy"]
