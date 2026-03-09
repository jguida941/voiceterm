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
from .qss_base import qss_base
from .qss_controls import qss_controls
from .qss_navigation import qss_navigation
from .qss_panels import qss_panels
from .qss_summary import qss_summary
from .theme_tokens import default_theme_tokens


def build_operator_console_stylesheet_from_colors(
    colors: Mapping[str, str],
    tokens: Mapping[str, str] | None = None,
) -> str:
    """Return the shared stylesheet for an explicit semantic color mapping."""
    color = dict(colors)
    token = default_theme_tokens()
    if tokens is not None:
        token.update({key: str(value) for key, value in tokens.items()})
    return (
        qss_base(color, token)
        + qss_controls(color, token)
        + qss_panels(color, token)
        + qss_navigation(color, token)
        + qss_summary(color, token)
    )


def build_operator_console_stylesheet(theme_id: str = DEFAULT_THEME_ID) -> str:
    """Return the shared stylesheet for the Operator Console."""
    return build_operator_console_stylesheet_from_colors(
        resolve_theme(theme_id).colors
    )
