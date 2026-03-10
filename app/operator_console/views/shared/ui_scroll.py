"""Scroll-preserving text update helpers for QPlainTextEdit panels.

These functions let the operator stay at their current scroll position
when panel content refreshes on a 2-second poll cycle.
"""

from __future__ import annotations

try:
    from PyQt6.QtWidgets import QPlainTextEdit

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False


def _is_near_scroll_end(scrollbar: object, *, threshold: int = 4) -> bool:
    """Return whether a scrollbar is already close to its maximum value."""
    return scrollbar.maximum() - scrollbar.value() <= threshold


def replace_plain_text_preserving_scroll(widget: QPlainTextEdit, text: str) -> None:
    """Replace panel text without yanking the operator away from their viewport."""
    if widget.toPlainText() == text:
        return

    vertical_scrollbar = widget.verticalScrollBar()
    horizontal_scrollbar = widget.horizontalScrollBar()
    follow_vertical = _is_near_scroll_end(vertical_scrollbar)
    follow_horizontal = _is_near_scroll_end(horizontal_scrollbar)
    vertical_value = vertical_scrollbar.value()
    horizontal_value = horizontal_scrollbar.value()

    widget.setPlainText(text)

    if follow_vertical:
        vertical_scrollbar.setValue(vertical_scrollbar.maximum())
    else:
        vertical_scrollbar.setValue(min(vertical_value, vertical_scrollbar.maximum()))

    if follow_horizontal:
        horizontal_scrollbar.setValue(horizontal_scrollbar.maximum())
    else:
        horizontal_scrollbar.setValue(
            min(horizontal_value, horizontal_scrollbar.maximum())
        )


def append_plain_text_preserving_scroll(widget: QPlainTextEdit, text: str) -> None:
    """Append log/output text while preserving manual scroll when not tailing."""
    vertical_scrollbar = widget.verticalScrollBar()
    horizontal_scrollbar = widget.horizontalScrollBar()
    follow_vertical = _is_near_scroll_end(vertical_scrollbar)
    follow_horizontal = _is_near_scroll_end(horizontal_scrollbar)
    vertical_value = vertical_scrollbar.value()
    horizontal_value = horizontal_scrollbar.value()

    cursor = widget.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    cursor.insertText(text)
    widget.setTextCursor(cursor)

    if follow_vertical:
        vertical_scrollbar.setValue(vertical_scrollbar.maximum())
    else:
        vertical_scrollbar.setValue(min(vertical_value, vertical_scrollbar.maximum()))

    if follow_horizontal:
        horizontal_scrollbar.setValue(horizontal_scrollbar.maximum())
    else:
        horizontal_scrollbar.setValue(
            min(horizontal_value, horizontal_scrollbar.maximum())
        )
