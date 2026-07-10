"""Operator approval command helpers for the Operator Console."""

from __future__ import annotations

from ...workflows import (
    OPERATOR_DECISION_MODULE,
    build_operator_decision_command,
    parse_operator_decision_report,
)
from ...state.core.models import ApprovalRequest
from .ui_commands import CommandActionsMixin


class OperatorDecisionMixin:
    """Typed approval-routing helpers and completion handling."""

    def record_decision(
        self,
        decision: str,
        *,
        approval: ApprovalRequest | None = None,
        note: str = "",
    ) -> None:
        approval = self._resolve_operator_decision_approval(approval)
        if approval is None:
            return

        command = build_operator_decision_command(
            approval=approval,
            decision=decision,
            note=note,
            output_format="json",
        )
        self._start_command(
            command,
            context={
                "flow": "operator_decision",
                "decision": decision,
                "packet_id": approval.packet_id,
            },
            busy_label=f"{decision.title()}...",
        )

    def _on_approval_decision(
        self, decision: str, approval: object, note: str
    ) -> None:
        if not isinstance(approval, ApprovalRequest):
            return
        self.record_decision(decision, approval=approval, note=note)

    def _describe_command(self, command: list[str]) -> str:
        if len(command) >= 7 and command[1:3] == ["-m", OPERATOR_DECISION_MODULE]:
            try:
                decision = command[command.index("--decision") + 1]
            except (ValueError, IndexError):
                return "Approval"
            if decision == "approve":
                return "Approve"
            if decision == "deny":
                return "Deny"
            return "Approval"
        return CommandActionsMixin._describe_command(self, command)

    def _finish_operator_decision(
        self,
        *,
        exit_code: int,
        active_context: dict[str, object],
        stdout: str,
        stderr: str,
    ) -> None:
        decision = str(active_context.get("decision", "approval")).strip() or "approval"
        packet_id = str(active_context.get("packet_id", "")).strip() or "(unknown packet)"
        message = ""
        report: dict[str, object] | None = None
        if stdout.strip():
            try:
                report = parse_operator_decision_report(stdout.strip())
            except ValueError:
                report = None

        if isinstance(report, dict):
            raw_message = report.get("message")
            if isinstance(raw_message, str) and raw_message.strip():
                message = raw_message.strip()

        if exit_code == 0 and isinstance(report, dict) and bool(report.get("ok")):
            if not message:
                message = f"Recorded operator {decision} artifact for {packet_id}."
            self.approval_panel.clear_note()
            self._append_output(f"[Operator Decision] {message}\n")
            self._record_event(
                "INFO",
                "operator_decision_recorded",
                "Recorded operator decision through the typed wrapper command",
                details={
                    "decision": decision,
                    "packet_id": packet_id,
                    "typed_action_mode": report.get("typed_action_mode"),
                    "devctl_review_channel_action_available": report.get(
                        "devctl_review_channel_action_available"
                    ),
                    "artifact": report.get("artifact"),
                },
            )
            self.statusBar().showMessage(message)
            return

        if not message:
            message = self._first_visible_line(stderr)
        if not message:
            message = f"Operator {decision} command failed for {packet_id}."
        self._append_output(f"[Operator Decision] {message}\n")
        self._record_event(
            self._completion_level(False, exit_code),
            "operator_decision_failed",
            "Typed operator decision command did not report success",
            details={
                "decision": decision,
                "packet_id": packet_id,
                "exit_code": exit_code,
            },
        )
        self.statusBar().showMessage(message)
