"""Generic command execution helpers for the Operator Console."""

from __future__ import annotations

from ...workflows import (
    build_process_audit_command,
    build_status_command,
    build_triage_command,
    render_command,
)

try:
    from PyQt6.QtCore import QProcess
except ImportError:
    QProcess = None


class CommandActionsMixin:
    """Repo-owned subprocess lifecycle and generic command actions."""

    def show_ci_status(self) -> None:
        self._start_command(
            build_status_command(include_ci=True),
            busy_label="CI...",
            busy_buttons=self._ci_action_buttons(),
        )

    def run_triage(self) -> None:
        self._start_command(
            build_triage_command(include_ci=True),
            busy_label="Triage...",
            busy_buttons=self._triage_action_buttons(),
        )

    def run_process_audit(self) -> None:
        self._start_command(
            build_process_audit_command(strict=True),
            busy_label="Audit...",
            busy_buttons=self._process_audit_action_buttons(),
        )

    def _start_command(
        self,
        command: list[str],
        *,
        context: dict[str, object] | None = None,
        busy_label: str | None = None,
        busy_buttons: tuple[object, ...] | None = None,
    ) -> bool:
        if self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning:
            self._append_output("An Operator Console command is already running.\n")
            self._reveal_output_surface("command_output")
            self._record_event(
                "WARNING",
                "command_rejected",
                "Rejected overlapping Operator Console command",
                details={"command": command},
            )
            self.statusBar().showMessage("A command is already running.")
            return False

        command_label = self._describe_command(command)
        self._append_output(f"$ {render_command(command)}\n")
        self._reveal_output_surface("command_output")
        self._set_command_controls_busy(
            True,
            label=busy_label or f"{command_label}...",
            busy_buttons=busy_buttons,
        )
        self._record_event(
            "INFO",
            "command_started",
            "Starting Operator Console command",
            details={
                "command": command,
                "command_label": command_label,
                "context": context or {},
            },
        )
        self.statusBar().showMessage(
            f"{command_label} started. Showing Launcher Output."
        )
        process = QProcess(self)
        process.setWorkingDirectory(str(self.repo_root))
        process.setProgram(command[0])
        process.setArguments(command[1:])
        process.readyReadStandardOutput.connect(
            lambda: self._handle_process_output(process, "stdout", "INFO")
        )
        process.readyReadStandardError.connect(
            lambda: self._handle_process_output(process, "stderr", "ERROR")
        )
        process.errorOccurred.connect(
            lambda error: self._on_process_error(process, error)
        )
        process.finished.connect(self._on_process_finished)
        self._process = process
        self._active_command_label = command_label
        self._active_command_context = dict(context or {})
        self._active_command_stdout = ""
        self._active_command_stderr = ""
        process.start()
        return True

    def _capture_completed_process(
        self, exit_code: int
    ) -> tuple[dict[str, object], str, str]:
        active_context = dict(self._active_command_context or {})
        stdout = self._active_command_stdout
        stderr = self._active_command_stderr
        self._append_output(f"\n[process exited with code {exit_code}]\n")
        self._record_event(
            "ERROR" if exit_code else "INFO",
            "command_finished",
            "Operator Console command finished",
            details={"exit_code": exit_code, "context": active_context},
        )
        self._reset_active_command_state()
        return active_context, stdout, stderr

    def _finish_captured_process(
        self,
        *,
        exit_code: int,
        active_context: dict[str, object],
        stdout: str,
        stderr: str,
    ) -> bool:
        if (
            active_context.get("flow") == "start_swarm"
            and isinstance(active_context.get("step"), str)
            and self._handle_start_swarm_completion(
                step=active_context["step"],
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
            )
        ):
            return True

        self._set_command_controls_busy(False)
        self.statusBar().showMessage(f"Command finished with exit code {exit_code}.")
        self._process = None
        self.refresh_snapshot()
        return False

    def _on_process_finished(self, exit_code: int, _exit_status: object) -> None:
        active_context, stdout, stderr = self._capture_completed_process(exit_code)
        self._finish_captured_process(
            exit_code=exit_code,
            active_context=active_context,
            stdout=stdout,
            stderr=stderr,
        )

    def _on_process_error(self, process: QProcess, error: object) -> None:
        """Surface start failures immediately instead of looking inert."""
        if process is not self._process:
            return
        failed_to_start = error == QProcess.ProcessError.FailedToStart
        if not failed_to_start:
            return

        command_label = getattr(self, "_active_command_label", None) or "Command"
        error_text = process.errorString().strip()
        if error_text:
            message = f"{command_label} could not start: {error_text}"
        else:
            message = f"{command_label} could not start."
        self._append_output(f"[process error] {message}\n")
        self._reveal_output_surface("command_output")
        self._record_event(
            "ERROR",
            "command_failed_to_start",
            "Operator Console command failed before process startup",
            details={
                "command_label": command_label,
                "context": self._active_command_context or {},
            },
        )
        self._reset_active_command_state()
        self._set_command_controls_busy(False)
        self.statusBar().showMessage(message)

    def _handle_process_output(
        self,
        process: QProcess,
        stream_name: str,
        level: str,
    ) -> None:
        raw = (
            bytes(process.readAllStandardOutput())
            if stream_name == "stdout"
            else bytes(process.readAllStandardError())
        )
        text = raw.decode("utf-8", errors="replace")
        if not text:
            return
        if stream_name == "stdout":
            self._active_command_stdout += text
        else:
            self._active_command_stderr += text
        self._append_output(text)
        self.diagnostics.append_command_output(stream_name=stream_name, text=text)
        preview = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if preview:
            self._record_event(
                level,
                f"command_{stream_name}",
                f"{stream_name} chunk received",
                details={
                    "preview": preview[:240],
                    "line_count": len([line for line in text.splitlines() if line.strip()]),
                },
            )

    def _reset_active_command_state(self) -> None:
        """Clear tracked state for the currently running command."""
        self._process = None
        self._active_command_label = None
        self._active_command_context = None
        self._active_command_stdout = ""
        self._active_command_stderr = ""

    def _describe_command(self, command: list[str]) -> str:
        """Return a short operator-facing label for a command."""
        if "process-audit" in command:
            return "Process Audit"
        if "orchestrate-status" in command:
            return "Workflow Audit"
        if "swarm_run" in command:
            return "Plan Loop"
        if "triage" in command:
            return "Triage"
        if "status" in command:
            return "CI Status"
        if "rollover" in command:
            return "Rollover"
        if "--action" in command and "post" in command:
            return "Live Summary"
        if "--dry-run" in command:
            return "Dry Run"
        if "launch" in command:
            return "Launch"
        return "Command"

    def _first_visible_line(self, text: str) -> str:
        for line in text.splitlines():
            if line.strip():
                return line.strip()
        return ""
