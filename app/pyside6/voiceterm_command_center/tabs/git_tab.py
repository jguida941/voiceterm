"""Git-focused operations tab."""

from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from voiceterm_command_center.runner import ProcessRunner


class GitTab(QWidget):
    """Run common repository operations from one tab."""

    PRESETS: tuple[tuple[str, str], ...] = (
        ("Status (short)", "git status --short"),
        ("Fetch origin", "git fetch origin"),
        ("Pull develop (ff-only)", "git pull --ff-only origin develop"),
        ("Push develop", "git push origin develop"),
        ("Recent log", "git log --oneline --decorate -n 20"),
        ("Branches (-vv)", "git branch -vv"),
    )

    def __init__(self) -> None:
        super().__init__()
        self._runner = ProcessRunner(self)

        self._preset_box = QComboBox()
        for label, _command in self.PRESETS:
            self._preset_box.addItem(label)

        self._run_btn = QPushButton("Run")
        self._stop_btn = QPushButton("Stop")
        self._status = QLabel("Idle")
        self._output = QTextEdit()
        self._output.setReadOnly(True)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Preset"))
        controls.addWidget(self._preset_box, 1)
        controls.addWidget(self._run_btn)
        controls.addWidget(self._stop_btn)
        controls.addWidget(self._status, 1)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self._output, 1)
        self.setLayout(layout)

        self._run_btn.clicked.connect(self._run_selected)
        self._stop_btn.clicked.connect(self._runner.terminate)
        self._runner.started.connect(self._append)
        self._runner.output.connect(self._append)
        self._runner.error.connect(self._append)
        self._runner.finished.connect(self._on_finished)
        self._runner.busy_changed.connect(self._on_busy_changed)
        self._on_busy_changed(False)

    def _run_selected(self) -> None:
        label, command = self.PRESETS[self._preset_box.currentIndex()]
        if self._runner.run_shell(command):
            self._status.setText(f"Running: {label}")

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
        self._preset_box.setEnabled(not busy)

