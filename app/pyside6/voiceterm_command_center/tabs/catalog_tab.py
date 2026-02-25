"""Full command catalog tab."""

from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from voiceterm_command_center.command_catalog import CommandSpec, all_commands
from voiceterm_command_center.runner import ProcessRunner


class CatalogTab(QWidget):
    """Search, inspect, and execute catalog commands."""

    def __init__(self) -> None:
        super().__init__()
        self._runner = ProcessRunner(self)
        self._commands = all_commands()
        self._visible_commands: list[CommandSpec] = []

        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter commands by label, group, or description")
        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._run_btn = QPushButton("Run Selected Command")
        self._stop_btn = QPushButton("Stop")
        self._status = QLabel("Idle")

        left = QVBoxLayout()
        left.addWidget(self._filter)
        left.addWidget(self._list, 1)

        actions = QHBoxLayout()
        actions.addWidget(self._run_btn)
        actions.addWidget(self._stop_btn)
        actions.addWidget(self._status, 1)

        right = QVBoxLayout()
        right.addWidget(QLabel("Command Detail"))
        right.addWidget(self._detail, 1)
        right.addLayout(actions)
        right.addWidget(QLabel("Execution Output"))
        right.addWidget(self._output, 2)

        layout = QHBoxLayout()
        layout.addLayout(left, 1)
        layout.addLayout(right, 2)
        self.setLayout(layout)

        self._filter.textChanged.connect(self._refresh_list)
        self._list.currentRowChanged.connect(self._show_details)
        self._run_btn.clicked.connect(self._run_selected)
        self._stop_btn.clicked.connect(self._runner.terminate)

        self._runner.started.connect(self._append_output)
        self._runner.output.connect(self._append_output)
        self._runner.error.connect(self._append_output)
        self._runner.finished.connect(self._on_finished)
        self._runner.busy_changed.connect(self._on_busy_changed)
        self._on_busy_changed(False)

        self._refresh_list()

    def _refresh_list(self) -> None:
        needle = self._filter.text().strip().lower()
        grouped: dict[str, list[CommandSpec]] = defaultdict(list)
        for cmd in self._commands:
            haystack = f"{cmd.group} {cmd.label} {cmd.description} {cmd.command}".lower()
            if not needle or needle in haystack:
                grouped[cmd.group].append(cmd)

        self._list.clear()
        self._visible_commands = []
        for group in sorted(grouped):
            for cmd in grouped[group]:
                self._visible_commands.append(cmd)
                item = QListWidgetItem(f"[{cmd.group}] {cmd.label}")
                self._list.addItem(item)

        if self._visible_commands:
            self._list.setCurrentRow(0)
        else:
            self._detail.setPlainText("No commands match this filter.")

    def _show_details(self, row: int) -> None:
        if row < 0 or row >= len(self._visible_commands):
            self._detail.setPlainText("")
            return
        cmd = self._visible_commands[row]
        self._detail.setPlainText(
            "\n".join(
                [
                    f"Group: {cmd.group}",
                    f"Label: {cmd.label}",
                    "",
                    cmd.description,
                    "",
                    "Command:",
                    cmd.command,
                ]
            )
        )

    def _run_selected(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= len(self._visible_commands):
            return
        cmd = self._visible_commands[row]
        if self._runner.run_shell(cmd.command):
            self._status.setText(f"Running: {cmd.label}")

    def _append_output(self, text: str) -> None:
        self._output.moveCursor(QTextCursor.End)
        self._output.insertPlainText(text)
        self._output.moveCursor(QTextCursor.End)

    def _on_finished(self, code: int, _payload: str) -> None:
        self._append_output(f"\n[exit {code}]\n\n")
        self._status.setText(f"Idle (last exit: {code})")

    def _on_busy_changed(self, busy: bool) -> None:
        self._run_btn.setEnabled(not busy)
        self._stop_btn.setEnabled(busy)
        self._list.setEnabled(not busy)
        self._filter.setEnabled(not busy)

