"""Reusable custom widgets for the Operator Console."""

from __future__ import annotations

try:
    from PyQt6.QtCore import QEvent, Qt
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

from .widgets_status_kv import (
    STATUS_ACTIVE,
    STATUS_IDLE,
    STATUS_STALE,
    STATUS_WARNING,
    CollapsibleKVRow,
    KeyValuePanel,
    SectionHeader,
    StatusIndicator,
)

_PROVIDER_BADGE_TEXT = {
    "codex": "CX",
    "claude": "CL",
    "cursor": "CR",
    "operator": "OP",
}

_PROVIDER_BADGE_TOOLTIP = {
    "codex": "Codex reviewer lane",
    "claude": "Claude implementer lane",
    "cursor": "Cursor editor lane",
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
    button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
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
        layout.addWidget(
            button,
            index // columns,
            index % columns,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )
    return container


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
        tooltip = _PROVIDER_BADGE_TOOLTIP.get(provider_id, f"{provider_name.strip() or 'Unknown'} lane")
        self.setToolTip(tooltip)
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)
        self.update()


class FlippableTextCard(QFrame if _PYQT_AVAILABLE else object):
    """Lane-styled card that flips between two read-only text panes."""

    def __init__(
        self,
        *,
        front_widget: QWidget,
        back_widget: QWidget,
        front_title: str,
        front_subtitle: str,
        back_title: str,
        back_subtitle: str,
        provider_name: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("LaneCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        self.provider_badge = ProviderBadge(provider_name or "operator")
        self.provider_badge.setVisible(bool(provider_name))
        header.addWidget(self.provider_badge)
        self.name_label = QLabel()
        self.name_label.setObjectName("LaneAgentName")
        header.addWidget(self.name_label)
        self.role_label = QLabel()
        self.role_label.setObjectName("LaneRoleLabel")
        header.addWidget(self.role_label)
        header.addStretch(1)
        self.flip_hint = QLabel("double-click to flip")
        self.flip_hint.setObjectName("LaneRoleLabel")
        header.addWidget(self.flip_hint)
        layout.addLayout(header)

        self._stack = QStackedWidget()
        self._stack.addWidget(front_widget)
        self._stack.addWidget(back_widget)
        layout.addWidget(self._stack, stretch=1)

        self._faces = (
            (front_title, front_subtitle, front_widget),
            (back_title, back_subtitle, back_widget),
        )
        self._showing_back = False
        self._install_flip_target(self)
        for widget in (front_widget, back_widget):
            self._install_flip_target(widget)
            if isinstance(widget, QPlainTextEdit):
                self._install_flip_target(widget.viewport())
        self._install_flip_target(self.name_label)
        self._install_flip_target(self.role_label)
        self._install_flip_target(self.flip_hint)
        if provider_name:
            self._install_flip_target(self.provider_badge)
        self._apply_face()

    @property
    def showing_back(self) -> bool:
        return self._showing_back

    @property
    def current_title(self) -> str:
        return self.name_label.text()

    def toggle_face(self) -> None:
        self._showing_back = not self._showing_back
        self._apply_face()

    def mouseDoubleClickEvent(self, event: object) -> None:
        self.toggle_face()
        super().mouseDoubleClickEvent(event)

    def eventFilter(self, watched: object, event: object) -> bool:
        if getattr(event, "type", None) is not None and event.type() == QEvent.Type.MouseButtonDblClick:
            self.toggle_face()
            return True
        return super().eventFilter(watched, event)

    def _apply_face(self) -> None:
        index = 1 if self._showing_back else 0
        title, subtitle, _widget = self._faces[index]
        self.name_label.setText(title)
        self.role_label.setText(f"— {subtitle}")
        self._stack.setCurrentIndex(index)

    def _install_flip_target(self, widget: QWidget) -> None:
        widget.installEventFilter(self)


class AgentSummaryCard(QFrame if _PYQT_AVAILABLE else object):
    """Compact card showing agent name, status, and key metrics."""

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
        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("CardStatusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
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
