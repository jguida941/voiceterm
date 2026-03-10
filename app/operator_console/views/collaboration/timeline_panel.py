"""Timeline panel for shared workflow event visibility."""

from __future__ import annotations

from ...collaboration.timeline_builder import TimelineEvent

try:
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object


_ACTOR_COLORS = {
    "codex": "#50b8ff",
    "claude": "#6ee7b7",
    "operator": "#f59e0b",
    "system": "#94a3b8",
}


class TimelinePanel(QWidget if _PYQT_AVAILABLE else object):
    """Simple filterable timeline for operator-facing event flow."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._events: tuple[TimelineEvent, ...] = ()
        self._visible_actors: set[str] = {"codex", "claude", "operator", "system"}
        self._filter_buttons: dict[str, QPushButton] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        filter_row.addWidget(self._title_label("Timeline"))
        for actor in ("codex", "claude", "operator", "system"):
            button = QPushButton(actor.title())
            button.setObjectName("SmallActionButton")
            button.setCheckable(True)
            button.setChecked(True)
            button.toggled.connect(
                lambda checked, actor_id=actor: self._toggle_actor(actor_id, checked)
            )
            filter_row.addWidget(button)
            self._filter_buttons[actor] = button
        filter_row.addStretch(1)
        root.addLayout(filter_row)

        self._list = QListWidget()
        self._list.setObjectName("TimelineList")
        root.addWidget(self._list, stretch=1)

    def set_events(self, events: tuple[TimelineEvent, ...]) -> None:
        """Replace timeline rows with the latest synthesized events."""
        self._events = events
        self._render()

    def visible_actors(self) -> tuple[str, ...]:
        """Return actors currently enabled by the filter toggles."""
        return tuple(actor for actor in ("codex", "claude", "operator", "system") if actor in self._visible_actors)

    def _toggle_actor(self, actor: str, checked: bool) -> None:
        if checked:
            self._visible_actors.add(actor)
        else:
            self._visible_actors.discard(actor)
        self._render()

    def _render(self) -> None:
        self._list.clear()
        for event in self._events:
            if event.actor not in self._visible_actors:
                continue
            badge = event.actor.upper()
            line = f"[{badge}] {event.title}\n{event.detail}\nsource: {event.source}"
            row = QListWidgetItem(line)
            row.setForeground(QColor(_ACTOR_COLORS.get(event.actor, _ACTOR_COLORS["system"])))
            self._list.addItem(row)
        if self._list.count() == 0:
            row = QListWidgetItem("No timeline events for current filters.")
            row.setForeground(QColor(_ACTOR_COLORS["system"]))
            self._list.addItem(row)

    @staticmethod
    def _title_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionHeaderLabel")
        return label
