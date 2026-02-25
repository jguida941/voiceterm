from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


@dataclass
class WorkflowRunRow:
    workflow: str
    conclusion: str
    event: str
    created_at: str
    sha: str
    url: str


class WorkflowRunsModel(QAbstractTableModel):
    HEADERS = ("Workflow", "Conclusion", "Event", "Created", "SHA", "URL")

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[WorkflowRunRow] = []

    def rowCount(self, _parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return len(self._rows)

    def columnCount(self, _parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None
        row = self._rows[index.row()]
        values = (
            row.workflow,
            row.conclusion,
            row.event,
            row.created_at,
            row.sha[:12],
            row.url,
        )
        if role == Qt.DisplayRole:
            return values[index.column()]
        if role == Qt.ToolTipRole and index.column() == 5:
            return row.url
        return None

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return None

    def replace(self, rows: list[WorkflowRunRow]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

