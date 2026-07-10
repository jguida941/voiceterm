"""Helpers for resolving theme settings into concrete metrics."""

from __future__ import annotations

from collections.abc import Mapping


def theme_bool(settings: Mapping[str, str], key: str, default: bool) -> bool:
    """Return a boolean-like theme setting."""

    value = str(settings.get(key, "true" if default else "false")).strip().lower()
    return value in {"1", "true", "yes", "on"}


def theme_choice(settings: Mapping[str, str], key: str, default: str) -> str:
    """Return a normalized select-style theme setting."""

    value = str(settings.get(key, default)).strip()
    return value or default


def theme_int(settings: Mapping[str, str], key: str, default: int) -> int:
    """Return an integer-like theme setting with a fallback."""

    try:
        return int(str(settings.get(key, default)).strip())
    except (TypeError, ValueError):
        return default


def resolved_radius(
    tokens: Mapping[str, str],
    components: Mapping[str, str],
    *,
    size: str = "default",
) -> int:
    """Return the effective radius for the selected corner profile."""

    key = {
        "small": "border_radius_small",
        "large": "border_radius_large",
    }.get(size, "border_radius")
    base = theme_int(tokens, key, 0)
    corner_style = theme_choice(components, "corner_style", "rounded")
    if corner_style == "square":
        return 0
    if corner_style == "pill":
        minimum = {
            "small": 10,
            "large": 18,
        }.get(size, 14)
        return max(base, minimum)
    return base


def resolved_border_width(
    tokens: Mapping[str, str],
    components: Mapping[str, str],
    *,
    focus: bool = False,
) -> int:
    """Return the effective border width for the selected border profile."""

    key = "border_width_focus" if focus else "border_width"
    base = theme_int(tokens, key, 1)
    border_style = theme_choice(components, "border_style", "soft")
    if border_style == "strong":
        return max(base, 2)
    if border_style == "minimal" and not focus:
        return 0
    return base
