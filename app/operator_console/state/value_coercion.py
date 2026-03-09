"""Shared value coercion helpers for Operator Console state projections."""

from __future__ import annotations


def safe_text(value: object) -> str | None:
    """Return a stripped non-empty string, otherwise ``None``."""
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    return None


def safe_int(value: object) -> int:
    """Coerce simple scalar values into an integer fallback."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0
