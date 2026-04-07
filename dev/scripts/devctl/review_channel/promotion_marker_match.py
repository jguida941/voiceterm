"""Marker matching helpers for bridge promotion readiness."""

from __future__ import annotations


def matches_any_marker(item: str, markers: tuple[str, ...]) -> bool:
    return any(matches_marker(item, marker) for marker in markers)


def matches_marker(item: str, marker: str) -> bool:
    normalized_item = item.strip().lower().rstrip(".")
    normalized_marker = marker.strip().lower()
    return (
        normalized_item == normalized_marker
        or normalized_item.startswith(f"{normalized_marker}:")
        or normalized_item.startswith(f"{normalized_marker} ")
    )
