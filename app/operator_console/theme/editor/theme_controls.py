"""Shared UI controls for the Operator Console theme editor.

Adapted from gitui's theme_controls.py (PySide6 → PyQt6).
"""

from __future__ import annotations

from ..colors import _mix, pick_contrasting_color
from ..runtime.theme_state import BUILTIN_PRESETS

try:
    from PyQt6.QtCore import pyqtSignal
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import QColorDialog, QPushButton, QWidget

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False


if _PYQT_AVAILABLE:

    _DEFAULT_SWATCH_COLOR = BUILTIN_PRESETS["Codex"].colors["accent"]
    _DEFAULT_SWATCH_FOREGROUND = BUILTIN_PRESETS["Codex"].colors["text"]
    _DEFAULT_SWATCH_BACKGROUND = BUILTIN_PRESETS["Codex"].colors["bg_top"]

    class ColorPickerButton(QPushButton):
        """Button that shows a color swatch and opens a picker on click."""

        color_changed = pyqtSignal(str)

        def __init__(
            self,
            color: str = _DEFAULT_SWATCH_COLOR,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)
            self._color = self._normalize_color(color)
            self._foreground_color = _DEFAULT_SWATCH_FOREGROUND
            self._background_color = _DEFAULT_SWATCH_BACKGROUND
            self.setFixedSize(70, 28)
            self._update_style()
            self.clicked.connect(self._pick_color)

        @property
        def color(self) -> str:
            return self._color

        @color.setter
        def color(self, value: str) -> None:
            normalized = self._normalize_color(value)
            if normalized == self._color:
                return
            self._color = normalized
            self._update_style()

        def set_reference_colors(
            self,
            *,
            foreground_color: str,
            background_color: str,
        ) -> None:
            next_foreground = self._normalize_reference_color(
                foreground_color,
                _DEFAULT_SWATCH_FOREGROUND,
            )
            next_background = self._normalize_reference_color(
                background_color,
                _DEFAULT_SWATCH_BACKGROUND,
            )
            if (
                next_foreground == self._foreground_color
                and next_background == self._background_color
            ):
                return
            self._foreground_color = next_foreground
            self._background_color = next_background
            self._update_style()

        def _update_style(self) -> None:
            text_color = pick_contrasting_color(
                self._color,
                dark=self._background_color,
                light=self._foreground_color,
            )
            border_color = _mix(self._color, self._background_color, 0.45)
            hover_border = _mix(self._color, self._foreground_color, 0.24)
            self.setStyleSheet(
                f"QPushButton {{ background-color: {self._color}; "
                f"color: {text_color}; border: 1px solid {border_color}; "
                f"border-radius: 4px; font-size: 10px; }}"
                f"QPushButton:hover {{ border: 2px solid {hover_border}; }}"
            )
            self.setText(self._color.upper()[:7])

        def _pick_color(self) -> None:
            color = QColorDialog.getColor(
                QColor(self._color), self, "Pick Color"
            )
            if color.isValid():
                self._color = color.name()
                self._update_style()
                self.color_changed.emit(self._color)

        def _normalize_color(self, value: str) -> str:
            color = QColor(value)
            if color.isValid():
                return color.name()
            return _DEFAULT_SWATCH_COLOR

        def _normalize_reference_color(self, value: str, fallback: str) -> str:
            color = QColor(value)
            if color.isValid():
                return color.name()
            return fallback

else:

    class ColorPickerButton:  # type: ignore[no-redef]
        """Stub when PyQt6 is not installed."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass
