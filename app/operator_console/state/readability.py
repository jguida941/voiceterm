"""Shared readability/audience-mode helpers for the Operator Console."""

from __future__ import annotations

AUDIENCE_MODES: tuple[str, ...] = ("simple", "technical")


def resolve_audience_mode(mode: str | None) -> str:
    """Normalize audience mode names with a safe default."""
    normalized = (mode or "").strip().lower()
    if normalized in AUDIENCE_MODES:
        return normalized
    return "simple"


def audience_mode_label(mode: str | None) -> str:
    """Return the human-facing label for an audience mode."""
    normalized = resolve_audience_mode(mode)
    return normalized.capitalize()
