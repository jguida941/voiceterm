"""Occupied-lane normalization for SessionPosture."""

from __future__ import annotations

_LANES = frozenset({"dashboard", "implementer", "observer", "reviewer"})


def normalize_occupied_lane(value: object) -> str:
    """Normalize a current occupied lane without treating grants as lanes."""
    lane = str(value or "").strip().lower().replace("-", "_")
    if lane == "operator":
        return "dashboard"
    if lane in _LANES:
        return lane
    return ""


__all__ = ["normalize_occupied_lane"]
