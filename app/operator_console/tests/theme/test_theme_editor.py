from __future__ import annotations

import os
import unittest

from app.operator_console.theme.editor import theme_editor as theme_editor_module
from app.operator_console.theme.editor import theme_preview as theme_preview_module

if theme_editor_module._PYQT_AVAILABLE:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication, QFrame, QPlainTextEdit, QTabWidget

    app = QApplication.instance() or QApplication([])


@unittest.skipUnless(theme_editor_module._PYQT_AVAILABLE, "PyQt6 is not installed")
class ThemeEditorDialogTests(unittest.TestCase):
    def test_theme_editor_constructs_with_left_workbench_controls(self) -> None:
        dialog = theme_editor_module.ThemeEditorDialog()
        dialog._engine.apply_builtin_theme("codex")
        dialog._sync_from_engine()

        self.assertEqual(dialog.windowTitle(), "Theme Editor")
        self.assertEqual(dialog._nav_list.count(), 9)
        self.assertEqual(dialog._nav_list.item(1).text(), "Surfaces")
        self.assertEqual(dialog._nav_list.item(3).text(), "Workflows")
        self.assertEqual(dialog._nav_list.item(6).text(), "Components")
        self.assertEqual(dialog._nav_list.item(7).text(), "Motion")
        self.assertIn("accent", dialog._color_controls)
        self.assertIn("font_size", dialog._token_controls)
        self.assertIn("button_style", dialog._component_controls)
        self.assertIn("page_transition", dialog._motion_controls)
        self.assertEqual(dialog._side_panel_tabs.count(), 3)
        self.assertEqual(dialog._side_panel_tabs.tabText(0), "Quick Tune")
        self.assertIn("accent", dialog._quick_color_controls)
        self.assertIn("toolbar_height", dialog._quick_token_controls)
        self.assertIn("button_style", dialog._quick_component_controls)
        self.assertIn("page_transition", dialog._quick_motion_controls)
        self.assertIn("codex", dialog._selection_summary_label.text().lower())
        self.assertIn("buttons:", dialog._selection_detail_label.text().lower())
        self.assertIn("Ready to export canonical overlay metadata", dialog._overlay_export_status.text())
        self.assertIn('base_theme = "codex"', dialog._overlay_export_preview.toPlainText())

        dialog.close()

    def test_theme_editor_can_switch_pages(self) -> None:
        dialog = theme_editor_module.ThemeEditorDialog()

        dialog._change_page(2)
        self.assertEqual(dialog._page_stack.currentIndex(), 2)

        dialog.close()

    def test_theme_editor_swatches_follow_live_theme_chrome(self) -> None:
        dialog = theme_editor_module.ThemeEditorDialog()
        dialog._engine.apply_builtin_theme("coral")
        dialog._sync_from_engine()

        state = dialog._engine.get_state()
        stylesheet = dialog._color_controls["accent"].styleSheet()

        self.assertIn(f"color: {state.colors['bg_top']};", stylesheet)
        self.assertNotIn("#000000", stylesheet)
        self.assertNotIn("#FFFFFF", stylesheet)

        dialog.close()

    def test_sync_motion_valid_int_values(self) -> None:
        """Valid integer motion values sync to QSpinBox correctly."""
        dialog = theme_editor_module.ThemeEditorDialog()
        # Modify engine internal state directly (get_state returns a copy)
        dialog._engine._state.motion["page_transition_ms"] = "300"
        dialog._engine._state.motion["pulse_duration_ms"] = "500"
        dialog._sync_from_engine()

        from PyQt6.QtWidgets import QSpinBox

        spin = dialog._motion_controls["page_transition_ms"]
        self.assertIsInstance(spin, QSpinBox)
        self.assertEqual(spin.value(), 300)

        spin2 = dialog._motion_controls["pulse_duration_ms"]
        self.assertIsInstance(spin2, QSpinBox)
        self.assertEqual(spin2.value(), 500)

        dialog.close()

    def test_sync_motion_nonnumeric_string_falls_back(self) -> None:
        """Non-numeric motion values like 'fast' must not crash the sync."""
        dialog = theme_editor_module.ThemeEditorDialog()
        dialog._engine._state.motion["page_transition_ms"] = "fast"
        dialog._engine._state.motion["pulse_duration_ms"] = "slow"

        # Must not raise ValueError
        dialog._sync_from_engine()

        from PyQt6.QtWidgets import QSpinBox

        spin = dialog._motion_controls["page_transition_ms"]
        self.assertIsInstance(spin, QSpinBox)
        # Falls back to spin box minimum (0 for these controls)
        self.assertEqual(spin.value(), spin.minimum())

        dialog.close()

    def test_sync_motion_missing_keys_handled(self) -> None:
        """Missing motion keys must not crash when state.motion is sparse."""
        dialog = theme_editor_module.ThemeEditorDialog()
        # Remove integer motion keys so .get() returns ""
        dialog._engine._state.motion.pop("page_transition_ms", None)
        dialog._engine._state.motion.pop("pulse_duration_ms", None)

        # Must not raise ValueError
        dialog._sync_from_engine()

        from PyQt6.QtWidgets import QSpinBox

        spin = dialog._motion_controls["page_transition_ms"]
        self.assertIsInstance(spin, QSpinBox)
        # Empty string falls back to the spin box minimum
        self.assertEqual(spin.value(), spin.minimum())

        dialog.close()


class SafeIntTests(unittest.TestCase):
    """Unit tests for _safe_int helper (pure Python, no PyQt dependency)."""

    def test_valid_int_string(self) -> None:
        self.assertEqual(theme_editor_module._safe_int("42", 0), 42)

    def test_valid_negative(self) -> None:
        self.assertEqual(theme_editor_module._safe_int("-5", 0), -5)

    def test_non_numeric_string_returns_fallback(self) -> None:
        self.assertEqual(theme_editor_module._safe_int("fast", 99), 99)

    def test_empty_string_returns_fallback(self) -> None:
        self.assertEqual(theme_editor_module._safe_int("", 0), 0)

    def test_none_returns_fallback(self) -> None:
        self.assertEqual(theme_editor_module._safe_int(None, 10), 10)

    def test_float_string_returns_fallback(self) -> None:
        # "3.5" is not a valid int literal
        self.assertEqual(theme_editor_module._safe_int("3.5", 0), 0)

    def test_actual_int_passthrough(self) -> None:
        self.assertEqual(theme_editor_module._safe_int(160, 0), 160)


@unittest.skipUnless(theme_preview_module._PYQT_AVAILABLE, "PyQt6 is not installed")
class ThemePreviewTests(unittest.TestCase):
    def test_preview_includes_toolbar_tabs_and_monitor_surfaces(self) -> None:
        preview = theme_preview_module.ThemePreview()

        self.assertIsNotNone(preview.findChild(QFrame, "Toolbar"))
        self.assertIsNotNone(preview.findChild(QTabWidget, "NavTabs"))
        self.assertIsNotNone(preview.findChild(QTabWidget, "MonitorTabs"))
        self.assertIsNotNone(preview.findChild(QPlainTextEdit, "PanelRawText"))
        self.assertIsNotNone(preview.findChild(QPlainTextEdit, "DiffView"))
        self.assertIsNotNone(preview.findChild(QFrame, "MotionPulseBar"))

    def test_preview_diff_highlighter_uses_updated_theme_colors(self) -> None:
        preview = theme_preview_module.ThemePreview()

        preview.set_preview_theme(
            {
                "status_active": "#112233",
                "danger": "#445566",
                "accent": "#778899",
                "text": "#aabbcc",
            }
        )

        self.assertIsNotNone(preview._diff_highlighter)
        added_bg = preview._diff_highlighter._added.background().color()
        removed_bg = preview._diff_highlighter._removed.background().color()
        self.assertEqual(added_bg.name(), "#112233")
        self.assertEqual(added_bg.alpha(), 25)
        self.assertEqual(removed_bg.name(), "#445566")
        self.assertEqual(removed_bg.alpha(), 25)


if __name__ == "__main__":
    unittest.main()
