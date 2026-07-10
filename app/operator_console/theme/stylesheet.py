"""QSS stylesheet compositor for the optional PyQt6 Operator Console.

Assembles the full stylesheet from modular QSS fragments:
  qss_base      — window backgrounds, typography, toolbar, status bar
  qss_controls  — buttons, inputs, combos, spinboxes, scrollbars
  qss_panels    — lane cards, KV rows, section headers
  qss_navigation — pill tabs, monitor tabs, sidebar nav
  qss_summary   — KPI cards, summary cards, role badges
"""

from __future__ import annotations

from collections.abc import Mapping

from .colors import DEFAULT_THEME_ID, resolve_theme
from .config.theme_components import default_component_settings
from .config.theme_motion import default_motion_settings
from .config.theme_tokens import default_theme_tokens
from .qss.qss_base import qss_base
from .qss.qss_controls import qss_controls
from .qss.qss_navigation import qss_navigation
from .qss.qss_panels import qss_panels
from .qss.qss_summary import qss_summary


def build_operator_console_stylesheet_from_colors(
    colors: Mapping[str, str],
    tokens: Mapping[str, str] | None = None,
    components: Mapping[str, str] | None = None,
    motion: Mapping[str, str] | None = None,
) -> str:
    """Return the shared stylesheet for an explicit semantic color mapping."""
    color = dict(colors)
    token = default_theme_tokens()
    component = default_component_settings()
    motion_settings = default_motion_settings()
    if tokens is not None:
        token.update({key: str(value) for key, value in tokens.items()})
    if components is not None:
        component.update({key: str(value) for key, value in components.items()})
    if motion is not None:
        motion_settings.update({key: str(value) for key, value in motion.items()})
    return (
        qss_base(color, token, component, motion_settings)
        + qss_controls(color, token, component, motion_settings)
        + qss_panels(color, token, component, motion_settings)
        + qss_navigation(color, token, component, motion_settings)
        + qss_summary(color, token, component, motion_settings)
    )


def build_operator_console_stylesheet(theme_id: str = DEFAULT_THEME_ID) -> str:
    """Return the shared stylesheet for the Operator Console."""
    return build_operator_console_stylesheet_from_colors(
        resolve_theme(theme_id).colors
    )
