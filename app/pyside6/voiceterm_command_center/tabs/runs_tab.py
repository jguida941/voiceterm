"""GitHub workflow-runs visualization tab."""

from __future__ import annotations

import json

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from voiceterm_command_center.models import WorkflowRunRow, WorkflowRunsModel
from voiceterm_command_center.runner import ProcessRunner


class RunsTab(QWidget):
    """Fetch and display recent GitHub workflow runs."""

    def __init__(self) -> None:
        super().__init__()
        self._runner = ProcessRunner(self)
        self._model = WorkflowRunsModel()
        self._pending_workflow_label = ""

        self._workflow_box = QComboBox()
        self._workflow_box.addItem("CodeRabbit Triage Bridge", "coderabbit_triage.yml")
        self._workflow_box.addItem("CodeRabbit Ralph Loop", "coderabbit_ralph_loop.yml")
        self._workflow_box.addItem("Release Preflight", "release_preflight.yml")
        self._workflow_box.addItem("Rust CI", "rust_ci.yml")
        self._branch_box = QComboBox()
        self._branch_box.addItems(["develop", "master"])
        self._limit_box = QComboBox()
        self._limit_box.addItems(["5", "10", "20", "50"])
        self._limit_box.setCurrentText("20")
        self._refresh_btn = QPushButton("Refresh")
        self._stop_btn = QPushButton("Stop")
        self._status = QLabel("Idle")

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table.horizontalHeader().setStretchLastSection(True)

        self._output = QTextEdit()
        self._output.setReadOnly(True)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Workflow"))
        controls.addWidget(self._workflow_box)
        controls.addWidget(QLabel("Branch"))
        controls.addWidget(self._branch_box)
        controls.addWidget(QLabel("Limit"))
        controls.addWidget(self._limit_box)
        controls.addWidget(self._refresh_btn)
        controls.addWidget(self._stop_btn)
        controls.addWidget(self._status, 1)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self._table, 2)
        layout.addWidget(QLabel("Command Output"))
        layout.addWidget(self._output, 1)
        self.setLayout(layout)

        self._refresh_btn.clicked.connect(self._refresh)
        self._stop_btn.clicked.connect(self._runner.terminate)
        self._runner.started.connect(self._append_output)
        self._runner.output.connect(self._append_output)
        self._runner.error.connect(self._append_output)
        self._runner.finished.connect(self._on_finished)
        self._runner.busy_changed.connect(self._on_busy_changed)
        self._on_busy_changed(False)

    def _refresh(self) -> None:
        workflow_file = self._workflow_box.currentData()
        branch = self._branch_box.currentText()
        limit = self._limit_box.currentText()
        self._pending_workflow_label = self._workflow_box.currentText()

        args = [
            "gh",
            "run",
            "list",
            "--workflow",
            str(workflow_file),
            "--branch",
            branch,
            "--limit",
            limit,
            "--json",
            "displayTitle,conclusion,event,createdAt,headSha,url",
        ]
        if self._runner.run(args):
            self._status.setText(f"Running: {self._pending_workflow_label}")

    def _on_finished(self, code: int, payload: str) -> None:
        self._append_output(f"\n[exit {code}]\n\n")
        if code != 0:
            self._status.setText(f"Failed (exit: {code})")
            return

        parsed = self._extract_json_array(payload)
        if parsed is None:
            self._status.setText("Failed (could not parse JSON)")
            return

        rows = [
            WorkflowRunRow(
                workflow=str(item.get("displayTitle") or self._pending_workflow_label),
                conclusion=str(item.get("conclusion") or ""),
                event=str(item.get("event") or ""),
                created_at=str(item.get("createdAt") or ""),
                sha=str(item.get("headSha") or ""),
                url=str(item.get("url") or ""),
            )
            for item in parsed
            if isinstance(item, dict)
        ]
        self._model.replace(rows)
        self._status.setText(f"Loaded {len(rows)} runs")

    def _append_output(self, text: str) -> None:
        self._output.moveCursor(QTextCursor.End)
        self._output.insertPlainText(text)
        self._output.moveCursor(QTextCursor.End)

    def _on_busy_changed(self, busy: bool) -> None:
        self._refresh_btn.setEnabled(not busy)
        self._stop_btn.setEnabled(busy)
        self._workflow_box.setEnabled(not busy)
        self._branch_box.setEnabled(not busy)
        self._limit_box.setEnabled(not busy)

    @staticmethod
    def _extract_json_array(payload: str) -> list[dict] | None:
        start = payload.find("[")
        end = payload.rfind("]")
        if start == -1 or end == -1 or end < start:
            return None
        chunk = payload[start : end + 1]
        try:
            parsed = json.loads(chunk)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, list):
            return None
        return parsed

