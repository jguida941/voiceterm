"""Shared numeric parsing helpers for devctl modules."""

from __future__ import annotations

from typing import Any


def to_int(value: Any, default: int = 0) -> int:
    """Convert value to int with a stable fallback."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float with a stable fallback."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_optional_float(
    value: Any, default: float | None = None
) -> float | None:
    """Convert optional value to float with a nullable fallback."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
