"""Process-result dispatch and operator-decision helpers for the Operator Console."""

from __future__ import annotations

from .ui_commands import CommandActionsMixin


class ProcessResultsMixin:
    """Process completion routing layered on top of generic subprocess handling."""

    def _on_process_finished(self, exit_code: int, exit_status: object) -> None:
        active_context, stdout, stderr = self._capture_completed_process(exit_code)
        if self._finish_plan_loop_preflight(
            exit_code=exit_code,
            active_context=active_context,
            stdout=stdout,
            stderr=stderr,
        ):
            return

        CommandActionsMixin._finish_captured_process(
            self,
            exit_code=exit_code,
            active_context=active_context,
            stdout=stdout,
            stderr=stderr,
        )

        flow = active_context.get("flow")
        if flow == "review_channel":
            self._finish_review_channel_command(
                exit_code=exit_code,
                active_context=active_context,
                stdout=stdout,
                stderr=stderr,
            )
            return
        if flow == "live_summary":
            self._finish_live_summary_command(
                exit_code=exit_code,
                active_context=active_context,
                stdout=stdout,
                stderr=stderr,
            )
            return
        if flow == "workflow_audit":
            self._finish_workflow_audit(
                exit_code=exit_code,
                active_context=active_context,
                stdout=stdout,
                stderr=stderr,
            )
            return
        if flow == "plan_loop":
            self._finish_plan_loop(
                exit_code=exit_code,
                active_context=active_context,
                stdout=stdout,
                stderr=stderr,
            )
            return
        if flow == "operator_decision":
            self._finish_operator_decision(
                exit_code=exit_code,
                active_context=active_context,
                stdout=stdout,
                stderr=stderr,
            )

    def _finish_plan_loop_preflight(
        self,
        *,
        exit_code: int,
        active_context: dict[str, object],
        stdout: str,
        stderr: str,
    ) -> bool:
        if active_context.get("flow") != "plan_loop_preflight":
            return False

        continued, message = self._handle_plan_loop_preflight_completion(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            preset_id=str(active_context.get("preset_id") or self._workflow_preset_id),
            plan_doc=str(active_context.get("plan_doc") or ""),
            mp_scope=str(active_context.get("mp_scope") or ""),
        )
        self._append_output(f"[Plan Loop] {message}\n")
        self._record_event(
            "INFO" if continued else self._completion_level(False, exit_code),
            "plan_loop_preflight_ok" if continued else "plan_loop_preflight_failed",
            "Plan loop preflight completed",
            details={
                "exit_code": exit_code,
                "message": message,
                "preset_id": active_context.get("preset_id"),
                "plan_doc": active_context.get("plan_doc"),
                "mp_scope": active_context.get("mp_scope"),
            },
        )
        self.statusBar().showMessage(message)
        if continued:
            return True
        self._set_command_controls_busy(False)
        self._process = None
        self.refresh_snapshot()
        return True

    def _finish_review_channel_command(
        self,
        *,
        exit_code: int,
        active_context: dict[str, object],
        stdout: str,
        stderr: str,
    ) -> None:
        action = str(active_context.get("action", "")).strip() or "launch"
        live = bool(active_context.get("live"))
        ok, message = self._review_channel_completion_message(
            action=action,
            live=live,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
        )
        command_label = "Rollover" if action == "rollover" else ("Live Launch" if live else "Dry Run")
        self._append_output(f"[{command_label}] {message}\n")
        self._record_event(
            "INFO" if ok else self._completion_level(False, exit_code),
            "review_channel_command_ok" if ok else "review_channel_command_failed",
            f"{command_label} command completed",
            details={
                "action": action,
                "live": live,
                "exit_code": exit_code,
                "message": message,
            },
        )
        self.statusBar().showMessage(message)

    def _finish_live_summary_command(
        self,
        *,
        exit_code: int,
        active_context: dict[str, object],
        stdout: str,
        stderr: str,
    ) -> None:
        target_agent = str(active_context.get("provider_id", "")).strip() or "codex"
        ok, message = self._live_summary_completion_message(
            target_agent=target_agent,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
        )
        self._append_output(f"[Live Summary] {message}\n")
        self._record_event(
            "INFO" if ok else self._completion_level(False, exit_code),
            "summary_live_ok" if ok else "summary_live_failed",
            "Live summary post command completed",
            details={
                "provider_id": target_agent,
                "report_id": active_context.get("report_id"),
                "report_title": active_context.get("report_title"),
                "exit_code": exit_code,
                "message": message,
            },
        )
        self.statusBar().showMessage(message)

    def _finish_workflow_audit(
        self,
        *,
        exit_code: int,
        active_context: dict[str, object],
        stdout: str,
        stderr: str,
    ) -> None:
        ok, message = self._workflow_audit_completion_message(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
        )
        self._set_workflow_feedback(
            level="active" if ok else "stale",
            label="Workflow Audit Green" if ok else "Workflow Audit Blocked",
            detail=message,
        )
        self._append_output(f"[Workflow Audit] {message}\n")
        self._record_event(
            "INFO" if ok else self._completion_level(False, exit_code),
            "workflow_audit_ok" if ok else "workflow_audit_failed",
            "Workflow audit command completed",
            details={
                "exit_code": exit_code,
                "message": message,
                "preset_id": active_context.get("preset_id"),
            },
        )
        self.statusBar().showMessage(message)

    def _finish_plan_loop(
        self,
        *,
        exit_code: int,
        active_context: dict[str, object],
        stdout: str,
        stderr: str,
    ) -> None:
        ok, message = self._plan_loop_completion_message(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
        )
        self._set_workflow_feedback(
            level="active" if ok else "stale",
            label="Loop Complete" if ok else "Loop Failed",
            detail=message,
        )
        self._append_output(f"[Plan Loop] {message}\n")
        self._record_event(
            "INFO" if ok else self._completion_level(False, exit_code),
            "plan_loop_ok" if ok else "plan_loop_failed",
            "Plan loop command completed",
            details={
                "exit_code": exit_code,
                "message": message,
                "preset_id": active_context.get("preset_id"),
                "plan_doc": active_context.get("plan_doc"),
                "mp_scope": active_context.get("mp_scope"),
            },
        )
        self.statusBar().showMessage(message)

    @staticmethod
    def _completion_level(ok: bool, exit_code: int) -> str:
        if ok:
            return "INFO"
        return "ERROR" if exit_code else "WARNING"
