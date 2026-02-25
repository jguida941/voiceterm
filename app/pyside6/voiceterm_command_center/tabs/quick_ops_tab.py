"""High-frequency operator commands tab."""

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

from voiceterm_command_center.command_catalog import CommandSpec, all_commands
from voiceterm_command_center.runner import ProcessRunner

QUICK_OP_IDS = (
    "runtime_release",
    "runtime_ci",
    "docs_strict",
    "orchestrate_status",
    "orchestrate_watch",
    "coderabbit_gate_develop",
    "coderabbit_ralph_gate_develop",
    "dispatch_ralph_report",
)


class QuickOpsTab(QWidget):
    """Run common command-center operations quickly."""

    def __init__(self) -> None:
        super().__init__()
        self._runner = ProcessRunner(self)
        self._presets = self._build_presets()

        self._preset_box = QComboBox()
        for preset in self._presets:
            self._preset_box.addItem(preset.label)
        self._run_btn = QPushButton("Run")
        self._stop_btn = QPushButton("Stop")
        self._status = QLabel("Idle")
        self._output = QTextEdit()
        self._output.setReadOnly(True)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Quick Operation"))
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

    @staticmethod
    def _build_presets() -> list[CommandSpec]:
        by_id = {cmd.id: cmd for cmd in all_commands()}
        presets = [by_id[cmd_id] for cmd_id in QUICK_OP_IDS if cmd_id in by_id]
        return presets

    def _run_selected(self) -> None:
        if not self._presets:
            return
        preset = self._presets[self._preset_box.currentIndex()]
        if self._runner.run_shell(preset.command):
            self._status.setText(f"Running: {preset.label}")

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

