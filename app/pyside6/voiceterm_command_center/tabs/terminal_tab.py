"""Ad-hoc terminal command tab."""

from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from voiceterm_command_center.runner import ProcessRunner


class TerminalTab(QWidget):
    """Run ad-hoc shell commands from the command center."""

    def __init__(self) -> None:
        super().__init__()
        self._runner = ProcessRunner(self)

        self._command = QLineEdit()
        self._command.setPlaceholderText("Enter a shell command (runs in repo root)")
        self._run_btn = QPushButton("Run")
        self._stop_btn = QPushButton("Stop")
        self._status = QLabel("Idle")
        self._output = QTextEdit()
        self._output.setReadOnly(True)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Command"))
        controls.addWidget(self._command, 1)
        controls.addWidget(self._run_btn)
        controls.addWidget(self._stop_btn)
        controls.addWidget(self._status, 1)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self._output, 1)
        self.setLayout(layout)

        self._run_btn.clicked.connect(self._run_command)
        self._stop_btn.clicked.connect(self._runner.terminate)
        self._command.returnPressed.connect(self._run_command)

        self._runner.started.connect(self._append)
        self._runner.output.connect(self._append)
        self._runner.error.connect(self._append)
        self._runner.finished.connect(self._on_finished)
        self._runner.busy_changed.connect(self._on_busy_changed)
        self._on_busy_changed(False)

    def _run_command(self) -> None:
        command = self._command.text().strip()
        if not command:
            return
        if self._runner.run_shell(command):
            self._status.setText("Running ad-hoc command")

    def _append(self, text: str) -> None:
        self._output.moveCursor(QTextCursor.End)
        self._output.insertPlainText(text)
        self._output.moveCursor(QTextCursor.End)

    def _on_finished(self, code: int, _payload: str) -> None:
        self._append(f"\n[exit {code}]\n\n")
        self._status.setText(f"Idle (last exit: {code})")

    def _on_busy_changed(self, busy: bool) -> None:
        self._run_btn.setEnabled(not busy)
        self._stop_btn.setEnabled(busy)
        self._command.setEnabled(not busy)

