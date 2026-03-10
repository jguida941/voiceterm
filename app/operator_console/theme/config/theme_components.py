"""Component-style settings for the Operator Console theme system."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeChoiceSpec:
    """Editable select-style metadata used by the theme engine and editor."""

    label: str
    default: str
    options: tuple[tuple[str, str], ...]


COMPONENT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "Chrome": (
        "corner_style",
        "border_style",
        "surface_style",
    ),
    "Controls": (
        "button_style",
        "toolbar_button_style",
        "input_style",
    ),
    "Navigation": (
        "nav_tab_style",
        "monitor_tab_style",
    ),
}


COMPONENT_SPECS: dict[str, ThemeChoiceSpec] = {
    "corner_style": ThemeChoiceSpec(
        label="Corner Style",
        default="rounded",
        options=(
            ("rounded", "Rounded"),
            ("square", "Square"),
            ("pill", "Pill"),
        ),
    ),
    "border_style": ThemeChoiceSpec(
        label="Border Style",
        default="soft",
        options=(
            ("soft", "Soft"),
            ("strong", "Strong"),
            ("minimal", "Minimal"),
        ),
    ),
    "surface_style": ThemeChoiceSpec(
        label="Surface Style",
        default="layered",
        options=(
            ("layered", "Layered"),
            ("flat", "Flat"),
            ("terminal", "Terminal"),
        ),
    ),
    "button_style": ThemeChoiceSpec(
        label="Primary Button Style",
        default="soft-fill",
        options=(
            ("soft-fill", "Soft Fill"),
            ("outline", "Outline"),
            ("solid", "Solid"),
        ),
    ),
    "toolbar_button_style": ThemeChoiceSpec(
        label="Toolbar Button Style",
        default="chip",
        options=(
            ("chip", "Chip"),
            ("outline", "Outline"),
            ("ghost", "Ghost"),
        ),
    ),
    "input_style": ThemeChoiceSpec(
        label="Input Style",
        default="inset",
        options=(
            ("inset", "Inset"),
            ("outline", "Outline"),
            ("flat", "Flat"),
        ),
    ),
    "nav_tab_style": ThemeChoiceSpec(
        label="Top Nav Tabs",
        default="underline",
        options=(
            ("underline", "Underline"),
            ("pill", "Pill"),
            ("boxed", "Boxed"),
        ),
    ),
    "monitor_tab_style": ThemeChoiceSpec(
        label="Monitor Tabs",
        default="boxed",
        options=(
            ("boxed", "Boxed"),
            ("pill", "Pill"),
            ("underline", "Underline"),
        ),
    ),
}


def default_component_settings() -> dict[str, str]:
    """Return the full default component-style mapping."""

    return {
        key: spec.default
        for key, spec in COMPONENT_SPECS.items()
    }
