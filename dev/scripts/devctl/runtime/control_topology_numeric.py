"""Numeric helpers for observed control topology."""

from __future__ import annotations

from collections.abc import Mapping


def supervised_conductor_count(
    *,
    supervised_conductor_count_value: int | None,
    runtime_counts: Mapping[str, object],
) -> int:
    """Return non-negative supervised conductor count."""
    if supervised_conductor_count_value is not None:
        return max(int_value(supervised_conductor_count_value), 0)
    return max(count(runtime_counts, "active_conductor_count"), 0)


def count(mapping: Mapping[str, object], *keys: str) -> int:
    """Return the maximum integer value found for any key."""
    return max((int_value(mapping.get(key)) for key in keys), default=0)


def int_value(value: object) -> int:
    """Normalize loose integer values used in runtime projections."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
