"""Shared non-color theme tokens for the Operator Console."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class ThemeTokenSpec:
    """Editable non-color token metadata used by the theme engine and editor."""

    label: str
    value_type: Literal["int", "text"]
    default: str
    minimum: int | None = None
    maximum: int | None = None
    step: int = 1


TOKEN_CATEGORIES: dict[str, tuple[str, ...]] = {
    "Typography": (
        "font_family",
        "font_family_mono",
        "font_size",
        "font_size_small",
        "font_size_large",
        "font_size_h1",
        "font_size_h2",
        "font_size_h3",
    ),
    "Metrics": (
        "border_radius",
        "border_radius_small",
        "border_radius_large",
        "border_width",
        "border_width_focus",
        "padding",
        "padding_small",
        "padding_large",
        "spacing",
        "margin",
        "button_min_width",
        "input_height",
        "toolbar_height",
        "scrollbar_width",
    ),
}

TOKEN_SPECS: dict[str, ThemeTokenSpec] = {
    "font_family": ThemeTokenSpec(
        label="UI Font Family",
        value_type="text",
        default='"Inter", "SF Pro Display", "Segoe UI Variable", system-ui, "Avenir Next", sans-serif',
    ),
    "font_family_mono": ThemeTokenSpec(
        label="Mono Font Family",
        value_type="text",
        default='"JetBrains Mono", "SF Mono", "Menlo", "Monaco", "DejaVu Sans Mono"',
    ),
    "font_size": ThemeTokenSpec("Base Font Size", "int", "14", 8, 24),
    "font_size_small": ThemeTokenSpec("Small Font Size", "int", "11", 8, 20),
    "font_size_large": ThemeTokenSpec("Large Font Size", "int", "15", 10, 28),
    "font_size_h1": ThemeTokenSpec("Heading 1 Size", "int", "22", 14, 40),
    "font_size_h2": ThemeTokenSpec("Heading 2 Size", "int", "16", 12, 32),
    "font_size_h3": ThemeTokenSpec("Heading 3 Size", "int", "13", 10, 24),
    "border_radius": ThemeTokenSpec("Border Radius", "int", "6", 0, 32),
    "border_radius_small": ThemeTokenSpec("Small Radius", "int", "4", 0, 24),
    "border_radius_large": ThemeTokenSpec("Large Radius", "int", "14", 0, 36),
    "border_width": ThemeTokenSpec("Border Width", "int", "1", 0, 6),
    "border_width_focus": ThemeTokenSpec("Focus Border Width", "int", "1", 0, 8),
    "padding": ThemeTokenSpec("Padding", "int", "8", 0, 24),
    "padding_small": ThemeTokenSpec("Small Padding", "int", "3", 0, 20),
    "padding_large": ThemeTokenSpec("Large Padding", "int", "12", 0, 32),
    "spacing": ThemeTokenSpec("Spacing", "int", "6", 0, 24),
    "margin": ThemeTokenSpec("Margin", "int", "8", 0, 24),
    "button_min_width": ThemeTokenSpec("Button Min Width", "int", "90", 40, 220),
    "input_height": ThemeTokenSpec("Input Height", "int", "32", 20, 72),
    "toolbar_height": ThemeTokenSpec("Toolbar Height", "int", "40", 24, 96),
    "scrollbar_width": ThemeTokenSpec("Scrollbar Width", "int", "14", 8, 28),
}


def default_theme_tokens() -> dict[str, str]:
    """Return the full default non-color token mapping."""
    return {
        key: spec.default
        for key, spec in TOKEN_SPECS.items()
    }
