from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PySide6.QtCore import QObject, QProcess, Signal


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


class ProcessRunner(QObject):
    started = Signal(str)
    output = Signal(str)
    error = Signal(str)
    finished = Signal(int, str)
    busy_changed = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._process = QProcess(self)
        self._busy = False
        self._buffer: list[str] = []

        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)

    @property
    def busy(self) -> bool:
        return self._busy

    def run(self, args: Sequence[str], *, cwd: Path | None = None) -> bool:
        if self._busy or not args:
            return False
        self._busy = True
        self._buffer = []
        self.busy_changed.emit(True)

        working_dir = str(cwd or repo_root())
        self._process.setWorkingDirectory(working_dir)

        program = args[0]
        argv = [str(part) for part in args[1:]]
        cmd_display = " ".join(str(part) for part in args)
        self.started.emit(f"$ {cmd_display}\n")
        self._process.start(program, argv)
        return True

    def run_shell(self, command: str, *, cwd: Path | None = None) -> bool:
        if not command.strip():
            return False
        return self.run(("zsh", "-lc", command), cwd=cwd)

    def terminate(self) -> None:
        if self._busy:
            self._process.kill()

    def _on_stdout(self) -> None:
        data = bytes(self._process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        if data:
            self._buffer.append(data)
            self.output.emit(data)

    def _on_stderr(self) -> None:
        data = bytes(self._process.readAllStandardError()).decode(
            "utf-8", errors="replace"
        )
        if data:
            self._buffer.append(data)
            self.error.emit(data)

    def _on_finished(self, code: int, _status: QProcess.ExitStatus) -> None:
        stdout = bytes(self._process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        stderr = bytes(self._process.readAllStandardError()).decode(
            "utf-8", errors="replace"
        )
        if stdout:
            self._buffer.append(stdout)
        if stderr:
            self._buffer.append(stderr)
        self._busy = False
        self.busy_changed.emit(False)
        self.finished.emit(code, "".join(self._buffer))
