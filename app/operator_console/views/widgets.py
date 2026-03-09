"""Reusable custom widgets for the Operator Console.

Provides structured display widgets that replace raw text dumps with
operator-friendly key-value summaries and status indicators.
"""

from __future__ import annotations

try:
    from PyQt6.QtCore import QSize, Qt
    from PyQt6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QSizePolicy,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object


# Status level constants used by the pure state layer and rendered here.
STATUS_ACTIVE = "active"
STATUS_WARNING = "warning"
STATUS_STALE = "stale"
STATUS_IDLE = "idle"

_PROVIDER_BADGE_TEXT = {
    "codex": "CX",
    "claude": "CL",
    "operator": "OP",
}

_PROVIDER_BADGE_TOOLTIP = {
    "codex": "Codex reviewer lane",
    "claude": "Claude implementer lane",
    "operator": "Human operator lane",
}


def _normalize_provider_id(provider_name: str) -> str:
    return provider_name.strip().lower()


def compact_display_text(text: str, *, limit: int = 140) -> str:
    """Collapse whitespace and trim long card copy for dense layouts."""
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    clipped = normalized[: max(limit - 1, 1)].rstrip()
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return f"{clipped.rstrip(' .,;:-')}..."


def configure_compact_button(button: QPushButton) -> QPushButton:
    """Keep workspace action buttons pill-sized instead of full-width."""
    button.setObjectName("SmallActionButton")
    button.setSizePolicy(
        QSizePolicy.Policy.Maximum,
        QSizePolicy.Policy.Fixed,
    )
    button.setAutoDefault(False)
    button.setDefault(False)
    return button


def build_compact_button_grid(
    buttons: tuple[QPushButton, ...],
    *,
    columns: int = 2,
    parent: QWidget | None = None,
) -> QWidget:
    """Lay out action buttons in a compact grid so data panels stay dominant."""
    container = QWidget(parent)
    container.setObjectName("CompactButtonGrid")
    layout = QGridLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(8)
    layout.setVerticalSpacing(8)

    for index, button in enumerate(buttons):
        configure_compact_button(button)
        row = index // columns
        column = index % columns
        layout.addWidget(
            button,
            row,
            column,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )

    return container


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


class ProviderBadge(QLabel if _PYQT_AVAILABLE else object):
    """Small provider badge used beside agent names."""

    def __init__(self, provider_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProviderBadge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._provider_id = ""
        self.set_provider(provider_name)

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def set_provider(self, provider_name: str) -> None:
        provider_id = _normalize_provider_id(provider_name)
        if provider_id == self._provider_id:
            return
        self._provider_id = provider_id
        self.setProperty("providerId", provider_id)
        badge_text = _PROVIDER_BADGE_TEXT.get(provider_id, provider_id[:2].upper() or "?")
        self.setText(badge_text)
        tooltip = _PROVIDER_BADGE_TOOLTIP.get(
            provider_id,
            f"{provider_name.strip() or 'Unknown'} lane",
        )
        self.setToolTip(tooltip)
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
        self.status_dot.set_level(level)

    def set_title(self, title: str) -> None:
        """Update the rendered lane title."""
        self.title_label.setText(title)


class CollapsibleKVRow(QFrame if _PYQT_AVAILABLE else object):
    """Click-to-expand key-value row for compact data display.

    Default state shows key + truncated value on one line.
    Click to expand and show the full value with word wrap.
    A chevron glyph indicates the current state.
    """

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
        self._label_widget.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred
        )
        self._label_widget.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        layout.addWidget(self._label_widget)

        self._value_widget = QLabel("")
        self._value_widget.setObjectName("KVValue")
        self._value_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout.addWidget(self._value_widget, stretch=1)

        self._apply_state()

    @property
    def key(self) -> str:
        return self._label_widget.text()

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
        else:
            self._chevron.setText("\u25b8")
            self._value_widget.setWordWrap(False)
            text = self._full_value
            if len(text) > self._TRUNCATE_LEN:
                text = text[: self._TRUNCATE_LEN - 1] + "\u2026"
            self._value_widget.setText(text)


class KeyValuePanel(QWidget if _PYQT_AVAILABLE else object):
    """Structured key-value display with a raw-text toggle.

    Replaces ``QPlainTextEdit`` text dumps with a two-column layout where
    the operator can see structured data at a glance, or flip to the raw
    section text for full context.
    """

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        # Header with status dot
        self.header = SectionHeader(title)
        outer.addWidget(self.header)

        # Stacked widget: page 0 = structured KV, page 1 = raw text
        self._stack = QStackedWidget()
        outer.addWidget(self._stack, stretch=1)

        # Page 0: structured key-value rows
        self._kv_container = QWidget()
        self._kv_container.setObjectName("KVContainer")
        self._kv_layout = QVBoxLayout(self._kv_container)
        self._kv_layout.setContentsMargins(4, 4, 4, 4)
        self._kv_layout.setSpacing(4)
        self._kv_layout.addStretch(1)

        kv_scroll = _make_scrollable(self._kv_container)
        self._stack.addWidget(kv_scroll)

        # Page 1: raw text
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

        # Toggle button
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
        """Update the header status indicator."""
        self.header.set_status(level)

    def set_title(self, title: str) -> None:
        """Update the panel header title."""
        self.header.set_title(title)

    def set_rows(self, rows: list[tuple[str, str]]) -> None:
        """Replace structured key-value content with collapsible rows.

        Rows that were previously expanded by the operator stay expanded
        across refresh cycles (keyed by label text).
        """
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
        """Update the raw text view content."""
        if self._raw_text.toPlainText() != text:
            self._raw_text.setPlainText(text)

    def _toggle_view(self) -> None:
        self._showing_raw = not self._showing_raw
        self._stack.setCurrentIndex(1 if self._showing_raw else 0)
        self._toggle_btn.setText(
            "View Structured" if self._showing_raw else "View Raw"
        )


class AgentSummaryCard(QFrame if _PYQT_AVAILABLE else object):
    """Compact card showing agent name, status, and key metrics.

    Used in the KPI header strip for at-a-glance system status.
    """

    def __init__(
        self,
        agent_name: str,
        role: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("AgentSummaryCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        # Top row: status dot + agent name
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        self.status_dot = StatusIndicator()
        top_row.addWidget(self.status_dot)

        self.provider_badge = ProviderBadge(agent_name)
        top_row.addWidget(self.provider_badge)

        self.name_label = QLabel(agent_name)
        self.name_label.setObjectName("CardAgentName")
        top_row.addWidget(self.name_label)
        top_row.addStretch(1)

        self.role_badge = QLabel(role)
        self.role_badge.setObjectName("RoleBadge")
        self.role_badge.setVisible(bool(role))
        top_row.addWidget(self.role_badge)

        layout.addLayout(top_row)

        self.lane_label = QLabel("")
        self.lane_label.setObjectName("CardLaneLabel")
        self.lane_label.setWordWrap(True)
        layout.addWidget(self.lane_label)

        # Status line
        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("CardStatusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Detail line
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("CardDetailLabel")
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)

        self.set_identity(agent_name=agent_name, role=role, lane_title="")

    def set_identity(self, *, agent_name: str, role: str, lane_title: str) -> None:
        """Update the card identity without changing its live status text."""
        self.provider_badge.set_provider(agent_name)
        self.name_label.setText(agent_name)
        self.role_badge.setText(role)
        self.role_badge.setVisible(bool(role))
        self.lane_label.setText(lane_title)

    def update_card(
        self,
        *,
        status_level: str = STATUS_IDLE,
        status_text: str = "Idle",
        detail_text: str = "",
    ) -> None:
        self.status_dot.set_level(status_level)
        self.status_label.setText(status_text)
        self.detail_label.setText(detail_text)


def _make_scrollable(widget: QWidget) -> QWidget:
    """Wrap a widget in a scroll area with transparent background."""
    from PyQt6.QtWidgets import QScrollArea

    scroll = QScrollArea()
    scroll.setObjectName("PanelScrollArea")
    scroll.viewport().setObjectName("PanelScrollViewport")
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    return scroll
