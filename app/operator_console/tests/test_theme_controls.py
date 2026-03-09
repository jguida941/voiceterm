from __future__ import annotations

import os
import unittest

from app.operator_console.theme import theme_controls as theme_controls_module
from app.operator_console.theme.theme_state import BUILTIN_PRESETS

if theme_controls_module._PYQT_AVAILABLE:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])


@unittest.skipUnless(theme_controls_module._PYQT_AVAILABLE, "PyQt6 is not installed")
class ColorPickerButtonTests(unittest.TestCase):
    def test_default_button_uses_builtin_theme_chrome_without_legacy_hardcoded_hover(self) -> None:
        button = theme_controls_module.ColorPickerButton()
        stylesheet = button.styleSheet()

        self.assertEqual(button.color, BUILTIN_PRESETS["Codex"].colors["accent"])
        self.assertIn(BUILTIN_PRESETS["Codex"].colors["accent"], stylesheet)
        self.assertIn(
            f"color: {BUILTIN_PRESETS['Codex'].colors['bg_top']};",
            stylesheet,
        )
        self.assertNotIn("#00FFAA", stylesheet)
        self.assertNotIn("border: 1px solid #555", stylesheet)
        self.assertNotIn("#000000", stylesheet)
        self.assertNotIn("#FFFFFF", stylesheet)

    def test_invalid_color_normalizes_to_builtin_accent(self) -> None:
        button = theme_controls_module.ColorPickerButton("not-a-color")

        self.assertEqual(button.color, BUILTIN_PRESETS["Codex"].colors["accent"])
        self.assertEqual(button.text(), BUILTIN_PRESETS["Codex"].colors["accent"].upper()[:7])

    def test_reference_colors_drive_button_contrast_and_chrome(self) -> None:
        button = theme_controls_module.ColorPickerButton("#f0f0f0")
        button.set_reference_colors(
            foreground_color="#ddeeff",
            background_color="#102030",
        )
        stylesheet = button.styleSheet()

        self.assertIn("color: #102030;", stylesheet)
        self.assertNotIn("#000000", stylesheet)
        self.assertNotIn("#FFFFFF", stylesheet)


if __name__ == "__main__":
    unittest.main()
