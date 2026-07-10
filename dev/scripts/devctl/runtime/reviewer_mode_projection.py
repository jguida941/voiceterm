"""Canonical helpers for reviewer-mode projection writes."""

from __future__ import annotations

from collections.abc import MutableMapping


def write_reviewer_mode(
    payload: MutableMapping[str, object],
    value: object,
) -> None:
    """Write reviewer_mode through the typed-authority chokepoint."""
    payload["reviewer_mode"] = value


def write_effective_reviewer_mode(
    payload: MutableMapping[str, object],
    value: object,
) -> None:
    """Write effective_reviewer_mode through the typed-authority chokepoint."""
    payload["effective_reviewer_mode"] = value


__all__ = ["write_effective_reviewer_mode", "write_reviewer_mode"]
