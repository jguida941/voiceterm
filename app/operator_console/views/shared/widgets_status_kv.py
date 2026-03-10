"""Status and key-value display widgets shared by Operator Console views."""

from __future__ import annotations

try:
    from PyQt6.QtCore import QSize, Qt
    from PyQt6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object

STATUS_ACTIVE = "active"
STATUS_WARNING = "warning"
STATUS_STALE = "stale"
STATUS_IDLE = "idle"


class StatusIndicator(QLabel if _PYQT_AVAILABLE else object):
    """Small colored dot indicating agent or system health."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(QSize(14, 14))
        self.setObjectName("StatusIndicator")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._level = STATUS_IDLE
        self.setProperty("statusLevel", self._level)
        self._refresh_style()

    @property
    def level(self) -> str:
        return self._level

    def set_level(self, level: str) -> None:
        if level == self._level:
            return
        self._level = level
        self.setProperty("statusLevel", level)
        self._refresh_style()

    def _refresh_style(self) -> None:
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)
        self.update()


class SectionHeader(QWidget if _PYQT_AVAILABLE else object):
    """Lane header with an inline status dot and title text."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(8)
        self.status_dot = StatusIndicator()
        layout.addWidget(self.status_dot)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("SectionHeaderLabel")
        layout.addWidget(self.title_label)
        layout.addStretch(1)

    def set_status(self, level: str) -> None:
        dot = self.status_dot
        dot.set_level(level)

    def set_title(self, title: str) -> None:
        label = self.title_label
        label.setText(title)


class CollapsibleKVRow(QFrame if _PYQT_AVAILABLE else object):
    """Click-to-expand key-value row for compact data display."""

    _TRUNCATE_LEN = 60

    def __init__(
        self,
        label: str,
        value: str,
        *,
        expanded: bool = False,
        toggle_callback: object = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("KVRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._expanded = expanded
        self._full_value = value
        self._toggle_callback = toggle_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        self._chevron = QLabel("\u25b8")
        self._chevron.setObjectName("KVChevron")
        self._chevron.setFixedWidth(12)
        self._chevron.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._chevron)
        self._label_widget = QLabel(label)
        self._label_widget.setObjectName("KVLabel")
        self._label_widget.setMinimumWidth(50)
        self._label_widget.setMaximumWidth(80)
        self._label_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self._label_widget.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._label_widget)
        self._value_widget = QLabel("")
        self._value_widget.setObjectName("KVValue")
        self._value_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._value_widget, stretch=1)
        self._apply_state()

    @property
    def key(self) -> str:
        text = self._label_widget.text()
        return text

    def mousePressEvent(self, event: object) -> None:
        self._expanded = not self._expanded
        self._apply_state()
        if self._toggle_callback is not None:
            self._toggle_callback(self._expanded)
        super().mousePressEvent(event)

    def _apply_state(self) -> None:
        if self._expanded:
            self._chevron.setText("\u25be")
            self._value_widget.setWordWrap(True)
            self._value_widget.setText(self._full_value)
            return
        self._chevron.setText("\u25b8")
        self._value_widget.setWordWrap(False)
        text = self._full_value
        if len(text) > self._TRUNCATE_LEN:
            text = text[: self._TRUNCATE_LEN - 1] + "\u2026"
        self._value_widget.setText(text)


class KeyValuePanel(QWidget if _PYQT_AVAILABLE else object):
    """Structured key-value display with a raw-text toggle."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)
        self.header = SectionHeader(title)
        outer.addWidget(self.header)
        self._stack = QStackedWidget()
        outer.addWidget(self._stack, stretch=1)
        self._kv_container = QWidget()
        self._kv_container.setObjectName("KVContainer")
        self._kv_layout = QVBoxLayout(self._kv_container)
        self._kv_layout.setContentsMargins(4, 4, 4, 4)
        self._kv_layout.setSpacing(4)
        self._kv_layout.addStretch(1)
        self._stack.addWidget(_make_scrollable(self._kv_container))
        self._raw_text = QPlainTextEdit()
        self._raw_text.setObjectName("PanelRawText")
        self._raw_text.setReadOnly(True)
        self._raw_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self._raw_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._raw_text.setToolTip(
            "Wrapped raw lane text. Open the detail dialog when you need the full "
            "structured view or an exact diff-style rendering."
        )
        self._stack.addWidget(self._raw_text)
        self._toggle_btn = QPushButton("View Raw")
        self._toggle_btn.setObjectName("SmallToggleButton")
        self._toggle_btn.setFixedHeight(24)
        self._toggle_btn.setToolTip(
            "Switch between the structured key/value summary and the wrapped raw lane text."
        )
        self._toggle_btn.clicked.connect(self._toggle_view)
        outer.addWidget(self._toggle_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self._showing_raw = False
        self._row_widgets: list[QWidget] = []
        self._expanded_keys: set[str] = set()

    def set_status(self, level: str) -> None:
        hdr = self.header
        hdr.set_status(level)

    def set_title(self, title: str) -> None:
        hdr = self.header
        hdr.set_title(title)

    def set_rows(self, rows: list[tuple[str, str]]) -> None:
        for widget in self._row_widgets:
            self._kv_layout.removeWidget(widget)
            widget.deleteLater()
        self._row_widgets.clear()
        insert_index = 0
        for label, value in rows:

            def make_toggle(key: str):
                def toggle(expanded: bool) -> None:
                    if expanded:
                        self._expanded_keys.add(key)
                    else:
                        self._expanded_keys.discard(key)

                return toggle

            row_widget = CollapsibleKVRow(
                label,
                value,
                expanded=label in self._expanded_keys,
                toggle_callback=make_toggle(label),
            )
            self._kv_layout.insertWidget(insert_index, row_widget)
            self._row_widgets.append(row_widget)
            insert_index += 1

    def set_raw_text(self, text: str) -> None:
        if self._raw_text.toPlainText() != text:
            self._raw_text.setPlainText(text)

    def _toggle_view(self) -> None:
        self._showing_raw = not self._showing_raw
        self._stack.setCurrentIndex(1 if self._showing_raw else 0)
        self._toggle_btn.setText("View Structured" if self._showing_raw else "View Raw")


def _make_scrollable(widget: QWidget) -> QWidget:
    scroll = QScrollArea()
    scroll.setObjectName("PanelScrollArea")
    scroll.viewport().setObjectName("PanelScrollViewport")
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    return scroll
