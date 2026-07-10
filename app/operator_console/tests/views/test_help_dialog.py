"""Tests for the in-app Operator Console help dialog."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.operator_console.views import help_dialog as help_dialog_module

if help_dialog_module._PYQT_AVAILABLE:
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])


@unittest.skipUnless(help_dialog_module._PYQT_AVAILABLE, "PyQt6 is not installed")
class OperatorHelpDialogTests(unittest.TestCase):
    def test_dialog_builds_expected_topics(self) -> None:
        dialog = help_dialog_module.OperatorHelpDialog()
        self.assertEqual(dialog.windowTitle(), "Operator Console Guide")
        self.assertEqual(dialog._tabs.count(), 5)
        dialog.close()

    def test_show_topic_selects_requested_tab(self) -> None:
        dialog = help_dialog_module.OperatorHelpDialog()
        dialog.show_topic("developer")
        self.assertEqual(dialog._tabs.tabText(dialog._tabs.currentIndex()), "Developer")
        dialog.close()


if __name__ == "__main__":
    unittest.main()
