"""Kanban-style task board backed by review-channel packets.

Presents review-channel packets as task tickets organized in columns
(Pending, In Progress, Review, Done). Each ticket is a real
``devctl review-channel`` packet — the board is a visual skin over
the same guarded state machine that AI agents use.
"""

from __future__ import annotations

from ...collaboration.conversation_state import AGENT_DISPLAY_NAMES
from ...collaboration.task_board_state import TaskBoardSnapshot, TaskTicket
from ..shared.widgets import compact_display_text, configure_compact_button

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object


_COLUMN_LABELS: tuple[tuple[str, str], ...] = (
    ("pending", "Pending"),
    ("in_progress", "In Progress"),
    ("review", "Review"),
    ("done", "Done"),
)


if _PYQT_AVAILABLE:

    class _TaskColumn(QWidget):
        """One column in the task board (e.g. Pending, In Progress)."""

        ticket_clicked = pyqtSignal(str)

        def __init__(
            self, column_id: str, label: str, parent: QWidget | None = None
        ) -> None:
            super().__init__(parent)
            self._column_id = column_id

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)

            header = QHBoxLayout()
            header.setSpacing(6)
            title = QLabel(label)
            title.setObjectName("LaneAgentName")
            header.addWidget(title)
            self._count = QLabel("0")
            self._count.setObjectName("ApprovalCountBadge")
            self._count.setFixedSize(22, 22)
            self._count.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.addWidget(self._count)
            header.addStretch(1)
            layout.addLayout(header)

            self._list = QListWidget()
            self._list.setObjectName("TaskColumnList")
            self._list.itemClicked.connect(self._on_click)
            layout.addWidget(self._list, stretch=1)

        def set_tickets(self, tickets: tuple[TaskTicket, ...]) -> None:
            """Replace column contents with fresh tickets."""
            self._list.clear()
            for ticket in tickets:
                agent = AGENT_DISPLAY_NAMES.get(
                    ticket.assigned_agent, ticket.assigned_agent
                )
                label = (
                    f"{agent}  |  "
                    f"{compact_display_text(ticket.summary, limit=60)}"
                )
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, ticket.ticket_id)
                item.setToolTip(
                    f"[{ticket.kind}] {ticket.summary}\n"
                    f"From: {ticket.from_agent} | "
                    f"Updated: {ticket.last_updated}"
                )
                self._list.addItem(item)
            self._count.setText(str(len(tickets)))

        def _on_click(self, item: QListWidgetItem) -> None:
            ticket_id = item.data(Qt.ItemDataRole.UserRole)
            if ticket_id:
                self.ticket_clicked.emit(ticket_id)

    class TaskBoardPanel(QWidget):
        """Kanban-style board of review-channel task tickets.

        API contract:
        - ``set_board(snapshot)`` — push new data each poll cycle
        - ``ticket_selected`` signal — emitted when a ticket card
          is clicked, carrying the ticket_id for filtering.
        """

        ticket_selected = pyqtSignal(str)

        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)

            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(6)

            header = QLabel("Task Board")
            header.setObjectName("SectionHeaderLabel")
            root.addWidget(header)

            columns_row = QHBoxLayout()
            columns_row.setSpacing(8)

            self._columns: dict[str, _TaskColumn] = {}
            for col_id, col_label in _COLUMN_LABELS:
                column = _TaskColumn(col_id, col_label)
                column.ticket_clicked.connect(self.ticket_selected.emit)
                self._columns[col_id] = column
                columns_row.addWidget(column)

            root.addLayout(columns_row, stretch=1)

        def set_board(self, snapshot: TaskBoardSnapshot) -> None:
            """Replace all columns with fresh ticket data."""
            self._columns["pending"].set_tickets(snapshot.pending)
            self._columns["in_progress"].set_tickets(snapshot.in_progress)
            self._columns["review"].set_tickets(snapshot.review)
            self._columns["done"].set_tickets(snapshot.done)

else:

    class TaskBoardPanel:  # type: ignore[no-redef]
        """Stub when PyQt6 is not installed."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def set_board(self, snapshot: object) -> None:
            pass
