from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication, QPlainTextEdit  # noqa: E402
except ImportError:
    QApplication = None
    QPlainTextEdit = None

from app.operator_console.views.shared.ui_scroll import (  # noqa: E402
    append_plain_text_preserving_scroll,
    replace_plain_text_preserving_scroll,
)


def _make_multiline_text(label: str, count: int = 200) -> str:
    return "\n".join(f"{label} line {index}" for index in range(count))


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class ScrollBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _make_widget(self) -> QPlainTextEdit:
        widget = QPlainTextEdit()
        widget.resize(480, 240)
        widget.show()
        self.app.processEvents()
        return widget

    def test_replace_preserves_manual_scroll_position(self) -> None:
        widget = self._make_widget()
        widget.setPlainText(_make_multiline_text("before"))
        self.app.processEvents()

        scroll_bar = widget.verticalScrollBar()
        scroll_bar.setValue(max(1, scroll_bar.maximum() // 2))
        expected_value = scroll_bar.value()

        replace_plain_text_preserving_scroll(widget, _make_multiline_text("after"))
        self.app.processEvents()

        self.assertEqual(scroll_bar.value(), min(expected_value, scroll_bar.maximum()))

    def test_replace_keeps_following_when_already_at_bottom(self) -> None:
        widget = self._make_widget()
        widget.setPlainText(_make_multiline_text("before"))
        self.app.processEvents()

        scroll_bar = widget.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

        replace_plain_text_preserving_scroll(widget, _make_multiline_text("after"))
        self.app.processEvents()

        self.assertEqual(scroll_bar.value(), scroll_bar.maximum())

    def test_append_preserves_manual_scroll_position(self) -> None:
        widget = self._make_widget()
        widget.setPlainText(_make_multiline_text("before"))
        self.app.processEvents()

        scroll_bar = widget.verticalScrollBar()
        scroll_bar.setValue(max(1, scroll_bar.maximum() // 2))
        expected_value = scroll_bar.value()

        append_plain_text_preserving_scroll(widget, "\nextra tail line")
        self.app.processEvents()

        self.assertEqual(scroll_bar.value(), min(expected_value, scroll_bar.maximum()))

    def test_append_keeps_following_when_already_at_bottom(self) -> None:
        widget = self._make_widget()
        widget.setPlainText(_make_multiline_text("before"))
        self.app.processEvents()

        scroll_bar = widget.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

        append_plain_text_preserving_scroll(widget, "\nextra tail line")
        self.app.processEvents()

        self.assertEqual(scroll_bar.value(), scroll_bar.maximum())


if __name__ == "__main__":
    unittest.main()
