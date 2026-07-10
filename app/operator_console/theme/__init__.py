"""Theme package — re-exports for backward compatibility."""

from .colors import (
    DEFAULT_THEME_ID,
    OperatorConsoleTheme,
    available_theme_ids,
    resolve_theme,
)
from .stylesheet import (
    build_operator_console_stylesheet,
    build_operator_console_stylesheet_from_colors,
)
from .runtime.theme_engine import ThemeEngine, get_engine, reset_engine
from .runtime.theme_state import ThemeState

try:
    from .editor import ThemeEditorDialog
except ImportError:
    ThemeEditorDialog = None  # type: ignore[assignment,misc]

try:
    from .editor import ColorPickerButton
except ImportError:
    ColorPickerButton = None  # type: ignore[assignment,misc]

__all__ = [
    "ColorPickerButton",
    "DEFAULT_THEME_ID",
    "OperatorConsoleTheme",
    "ThemeEditorDialog",
    "ThemeEngine",
    "ThemeState",
    "available_theme_ids",
    "build_operator_console_stylesheet",
    "build_operator_console_stylesheet_from_colors",
    "get_engine",
    "reset_engine",
    "resolve_theme",
]
