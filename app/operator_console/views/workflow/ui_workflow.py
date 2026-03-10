"""Workflow-launcher helpers for the Operator Console workflow package."""

from __future__ import annotations

from ...workflows import (
    build_orchestrate_status_command,
    build_swarm_run_command,
    evaluate_orchestrate_status_report,
    evaluate_swarm_run_report,
    parse_orchestrate_status_report,
    parse_swarm_run_report,
)
from ...workflows.workflow_presets import resolve_workflow_preset


class WorkflowControlsMixin:
    """Workflow preset syncing, launch commands, and button busy state."""

    def _sync_workflow_selector_from_home(self) -> None:
        preset_id = self.home_workspace.workflow_selector.currentData()
        if isinstance(preset_id, str):
            self._apply_workflow_preset(preset_id)

    def _sync_workflow_selector_from_activity(self) -> None:
        preset_id = self.activity_workspace.workflow_selector.currentData()
        if isinstance(preset_id, str):
            self._apply_workflow_preset(preset_id)

    def _apply_workflow_preset(self, preset_id: str, *, announce: bool = True) -> None:
        preset = resolve_workflow_preset(preset_id)
        self._workflow_preset_id = preset.preset_id
        for combo in self._workflow_selector_combos():
            index = combo.findData(preset.preset_id)
            if index >= 0:
                combo.blockSignals(True)
                try:
                    combo.setCurrentIndex(index)
                finally:
                    combo.blockSignals(False)
        self.home_workspace.set_workflow_preset(preset)
        self.activity_workspace.set_workflow_preset(preset)
        if announce:
            self.statusBar().showMessage(
                f"Workflow scope set to {preset.label} ({preset.mp_scope})."
            )

    def run_workflow_audit(self) -> None:
        """Run the orchestration audit from the current GUI workflow scope."""
        preset = resolve_workflow_preset(self._workflow_preset_id)
        detail = (
            f"Checking orchestrate-status for {preset.label} "
            f"({preset.mp_scope}) before the next loop or review action."
        )
        self._set_workflow_feedback(
            level="active",
            label="Workflow Audit Running",
            detail=detail,
        )
        started = self._start_command(
            build_orchestrate_status_command(output_format="json"),
            context={"flow": "workflow_audit", "preset_id": self._workflow_preset_id},
            busy_label="Audit...",
            busy_buttons=self._audit_action_buttons(),
        )
        if not started:
            self._set_workflow_feedback(
                level="stale",
                label="Workflow Audit Blocked",
                detail="Workflow audit could not start because another command is already running.",
            )

    def run_selected_plan_loop(self) -> None:
        """Audit first, then run the selected markdown plan through the loop."""
        preset = resolve_workflow_preset(self._workflow_preset_id)
        detail = (
            f"Checking orchestrate-status for {preset.label} "
            f"({preset.mp_scope}) before launching the continuous loop."
        )
        self._set_workflow_feedback(
            level="active",
            label="Loop Audit Running",
            detail=detail,
        )
        started = self._start_command(
            build_orchestrate_status_command(output_format="json"),
            context={
                "flow": "plan_loop_preflight",
                "preset_id": preset.preset_id,
                "plan_doc": preset.plan_doc,
                "mp_scope": preset.mp_scope,
            },
            busy_label="Audit...",
            busy_buttons=self._loop_action_buttons(),
        )
        if not started:
            self._set_workflow_feedback(
                level="stale",
                label="Loop Audit Blocked",
                detail="Loop preflight could not start because another command is already running.",
            )

    def _handle_plan_loop_preflight_completion(
        self,
        *,
        exit_code: int,
        stdout: str,
        stderr: str,
        preset_id: str,
        plan_doc: str,
        mp_scope: str,
    ) -> tuple[bool, str]:
        """Audit before loop launch so the GUI fails early and clearly."""
        ok, message = self._workflow_audit_completion_message(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
        )
        if not ok:
            blocked_message = f"Plan loop blocked: {message}"
            self._set_workflow_feedback(
                level="stale",
                label="Loop Blocked",
                detail=blocked_message,
            )
            return False, blocked_message

        started = self._start_command(
            build_swarm_run_command(
                plan_doc=plan_doc,
                mp_scope=mp_scope,
                output_format="json",
                continuous=True,
                continuous_max_cycles=10,
                feedback_sizing=True,
            ),
            context={
                "flow": "plan_loop",
                "preset_id": preset_id,
                "plan_doc": plan_doc,
                "mp_scope": mp_scope,
            },
            busy_label="Loop...",
            busy_buttons=self._loop_action_buttons(),
        )
        if not started:
            blocked_message = (
                f"Plan loop audit passed for {mp_scope}, but the loop command could not start."
            )
            self._set_workflow_feedback(
                level="stale",
                label="Loop Start Failed",
                detail=blocked_message,
            )
            return False, blocked_message

        launch_message = (
            f"Workflow audit ok for {mp_scope}. Launching the continuous plan loop."
        )
        self._set_workflow_feedback(
            level="active",
            label="Loop Launching",
            detail=launch_message,
        )
        return True, launch_message

    def _set_command_controls_busy(
        self,
        busy: bool,
        *,
        label: str | None = None,
        busy_buttons: tuple[object, ...] | None = None,
    ) -> None:
        """Disable all command buttons while one repo-owned action is running."""
        for button, default_text in self._command_button_defaults.items():
            button.setEnabled(not busy)
            if not busy:
                button.setText(default_text)

        for combo in self._workflow_selector_combos():
            combo.setEnabled(not busy)

        if busy:
            display_label = label or "Running..."
            for button in busy_buttons or ():
                if button in self._command_button_defaults:
                    button.setText(display_label)
            return

        self._refresh_live_terminal_controls()

    def _workflow_audit_completion_message(
        self,
        *,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> tuple[bool, str]:
        stripped_stdout = stdout.strip()
        if stripped_stdout:
            try:
                report = parse_orchestrate_status_report(stripped_stdout)
            except ValueError:
                detail = self._first_visible_line(stderr)
                if detail:
                    return False, detail
                return False, "Workflow audit did not return a readable JSON report."
            return evaluate_orchestrate_status_report(report)

        detail = self._first_visible_line(stderr)
        if detail:
            return False, detail
        fallback = "Workflow audit failed." if exit_code else "Workflow audit completed."
        return exit_code == 0, fallback

    def _plan_loop_completion_message(
        self,
        *,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> tuple[bool, str]:
        stripped_stdout = stdout.strip()
        if stripped_stdout:
            try:
                report = parse_swarm_run_report(stripped_stdout)
            except ValueError:
                detail = self._first_visible_line(stderr)
                if detail:
                    return False, detail
                return False, "Plan loop did not return a readable JSON report."
            return evaluate_swarm_run_report(report)

        detail = self._first_visible_line(stderr)
        if detail:
            return False, detail
        fallback = "Plan loop failed." if exit_code else "Plan loop completed."
        return exit_code == 0, fallback

    def _workflow_selector_combos(self) -> tuple[object, ...]:
        return (
            self.home_workspace.workflow_selector,
            self.activity_workspace.workflow_selector,
        )

    def _set_workflow_feedback(self, *, level: str, label: str, detail: str) -> None:
        """Mirror the latest workflow-controller state into both launchpads."""
        self.home_workspace.set_workflow_feedback(
            level=level,
            label=label,
            detail=detail,
        )
        self.activity_workspace.set_workflow_feedback(
            level=level,
            label=label,
            detail=detail,
        )

    def _audit_action_buttons(self) -> tuple[object, ...]:
        return (
            self.home_workspace.audit_button,
            self.activity_workspace.activity_audit_button,
        )

    def _loop_action_buttons(self) -> tuple[object, ...]:
        return (
            self.home_workspace.run_loop_button,
            self.activity_workspace.activity_run_loop_button,
        )

    def _dry_run_action_buttons(self) -> tuple[object, ...]:
        return (
            self.launch_dry_button,
            self.home_workspace.home_dry_run_button,
            self.activity_workspace.activity_dry_run_button,
        )

    def _review_action_buttons(self) -> tuple[object, ...]:
        return (
            self.home_workspace.start_swarm_button,
            self.activity_workspace.activity_start_swarm_button,
        )

    def _ci_action_buttons(self) -> tuple[object, ...]:
        return (self.activity_workspace.activity_ci_status_button,)

    def _triage_action_buttons(self) -> tuple[object, ...]:
        return (self.activity_workspace.activity_triage_button,)

    def _process_audit_action_buttons(self) -> tuple[object, ...]:
        return (self.activity_workspace.activity_process_audit_button,)
