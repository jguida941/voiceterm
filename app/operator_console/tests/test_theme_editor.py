from __future__ import annotations

import os
import unittest

from app.operator_console.theme import theme_editor as theme_editor_module
from app.operator_console.theme import theme_preview as theme_preview_module

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
        self.assertEqual(dialog._nav_list.count(), 7)
        self.assertEqual(dialog._nav_list.item(1).text(), "Surfaces")
        self.assertEqual(dialog._nav_list.item(3).text(), "Workflows")
        self.assertIn("accent", dialog._color_controls)
        self.assertIn("font_size", dialog._token_controls)
        self.assertEqual(dialog._side_panel_tabs.count(), 3)
        self.assertEqual(dialog._side_panel_tabs.tabText(0), "Quick Tune")
        self.assertIn("accent", dialog._quick_color_controls)
        self.assertIn("toolbar_height", dialog._quick_token_controls)
        self.assertIn("codex", dialog._selection_summary_label.text().lower())
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


@unittest.skipUnless(theme_preview_module._PYQT_AVAILABLE, "PyQt6 is not installed")
class ThemePreviewTests(unittest.TestCase):
    def test_preview_includes_toolbar_tabs_and_monitor_surfaces(self) -> None:
        preview = theme_preview_module.ThemePreview()

        self.assertIsNotNone(preview.findChild(QFrame, "Toolbar"))
        self.assertIsNotNone(preview.findChild(QTabWidget, "NavTabs"))
        self.assertIsNotNone(preview.findChild(QTabWidget, "MonitorTabs"))
        self.assertIsNotNone(preview.findChild(QPlainTextEdit, "PanelRawText"))
        self.assertIsNotNone(preview.findChild(QPlainTextEdit, "DiffView"))

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
