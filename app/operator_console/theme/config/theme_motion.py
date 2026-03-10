"""Motion settings for the Operator Console theme system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ThemeMotionSpec:
    """Editable motion metadata used by the theme engine and editor."""

    label: str
    value_type: Literal["bool", "int", "select"]
    default: str
    minimum: int | None = None
    maximum: int | None = None
    step: int = 1
    options: tuple[tuple[str, str], ...] = ()


MOTION_CATEGORIES: dict[str, tuple[str, ...]] = {
    "Behavior": (
        "motion_enabled",
        "page_transition",
        "hover_emphasis",
        "motion_curve",
    ),
    "Timing": (
        "page_transition_ms",
        "pulse_duration_ms",
    ),
}


MOTION_SPECS: dict[str, ThemeMotionSpec] = {
    "motion_enabled": ThemeMotionSpec(
        label="Enable Motion",
        value_type="bool",
        default="true",
    ),
    "page_transition": ThemeMotionSpec(
        label="Page Transition",
        value_type="select",
        default="fade",
        options=(
            ("fade", "Fade"),
            ("none", "None"),
        ),
    ),
    "hover_emphasis": ThemeMotionSpec(
        label="Hover Emphasis",
        value_type="select",
        default="soft",
        options=(
            ("soft", "Soft"),
            ("strong", "Strong"),
            ("none", "None"),
        ),
    ),
    "motion_curve": ThemeMotionSpec(
        label="Motion Curve",
        value_type="select",
        default="out-cubic",
        options=(
            ("out-cubic", "Out Cubic"),
            ("out-quad", "Out Quad"),
            ("linear", "Linear"),
        ),
    ),
    "page_transition_ms": ThemeMotionSpec(
        label="Page Transition ms",
        value_type="int",
        default="160",
        minimum=0,
        maximum=800,
        step=10,
    ),
    "pulse_duration_ms": ThemeMotionSpec(
        label="Pulse Duration ms",
        value_type="int",
        default="280",
        minimum=0,
        maximum=1200,
        step=10,
    ),
}


def default_motion_settings() -> dict[str, str]:
    """Return the full default motion mapping."""

    return {
        key: spec.default
        for key, spec in MOTION_SPECS.items()
    }
