"""Activity report and AI-summary actions for the Operator Console."""

from __future__ import annotations

from ...state.activity.activity_assist import build_summary_draft
from ...state.activity.activity_reports import build_activity_report
from ...workflows import (
    build_review_channel_post_command,
    evaluate_review_channel_post,
    parse_review_channel_report,
)
from ...state.core.readability import audience_mode_label, resolve_audience_mode


class ActivityActionsMixin:
    """Report-refresh and summary-request actions for the Activity surface."""

    def refresh_selected_report(self) -> None:
        snapshot = getattr(self, "_last_snapshot", None)
        if snapshot is None:
            return
        self._update_activity_report(snapshot)

    def generate_summary_draft(self) -> None:
        snapshot = getattr(self, "_last_snapshot", None)
        if snapshot is None:
            self.statusBar().showMessage(
                "Refresh the Activity view before generating an AI summary draft."
            )
            return

        draft = build_summary_draft(
            snapshot,
            report_id=self._current_report_id(),
            provider_id=self._current_summary_provider_id(),
            audience_mode=self._current_audience_mode(),
        )
        self._assist_text.setPlainText(draft.body)
        self._assist_meta_label.setText(" | ".join(draft.provenance))
        self._record_event(
            "INFO",
            "summary_draft_generated",
            "Generated a staged Activity-tab AI summary draft",
            details={
                "mode": draft.mode,
                "title": draft.title,
                "report_id": self._current_report_id(),
                "provider_id": self._current_summary_provider_id(),
                "pending_approvals": len(snapshot.pending_approvals),
                "warnings": list(snapshot.warnings),
            },
        )
        self.diagnostics.append_command_output(stream_name="assist", text=draft.body)
        self.statusBar().showMessage(f"{draft.title} ready in the Activity tab.")

    def generate_live_summary(self) -> None:
        """Post the selected Activity report as a live provider request."""
        snapshot = getattr(self, "_last_snapshot", None)
        if snapshot is None:
            self.statusBar().showMessage(
                "Refresh the Activity view before sending a live AI summary request."
            )
            return

        report_id = self._current_report_id()
        provider_id = self._current_summary_provider_id()
        report = build_activity_report(
            snapshot,
            report_id=report_id,
            audience_mode=self._current_audience_mode(),
        )
        packet_kind = self._live_summary_packet_kind(report_id)
        packet_summary = (
            f"Quality finding packet: {report.title}"
            if packet_kind == "finding"
            else f"Live AI summary request: {report.title}"
        )
        command = build_review_channel_post_command(
            to_agent=provider_id,
            summary=packet_summary,
            body=self._render_live_summary_body(
                provider_id=provider_id,
                report_title=report.title,
                report_summary=report.summary,
                report_body=report.body,
                packet_kind=packet_kind,
                quality_backlog=snapshot.quality_backlog if report_id == "quality" else None,
            ),
            output_format="json",
            kind=packet_kind,
            requested_action="review_only",
            policy_hint="review_only",
        )
        if not self._start_command(
            command,
            context={
                "flow": "live_summary",
                "provider_id": provider_id,
                "report_id": report_id,
                "report_title": report.title,
            },
            busy_label="Live Summary...",
            busy_buttons=(self.activity_workspace.assist_live_button,),
        ):
            return
        self._record_event(
            "INFO",
            "summary_live_requested",
            "Posted a live AI summary request through review-channel events",
            details={
                "provider_id": provider_id,
                "report_id": report_id,
                "report_title": report.title,
                "packet_kind": packet_kind,
            },
        )
        self.statusBar().showMessage(
            f"Posting live summary request to {provider_id.title()}..."
        )

    def _render_live_summary_body(
        self,
        *,
        provider_id: str,
        report_title: str,
        report_summary: str,
        report_body: str,
        packet_kind: str,
        quality_backlog: object = None,
    ) -> str:
        quality_lines: list[str] = []
        if packet_kind == "finding" and quality_backlog is not None:
            quality_lines.extend(self._quality_backlog_live_lines(quality_backlog))
        return "\n".join(
            [
                f"Live AI Summary Request ({provider_id.title()})",
                "=" * 40,
                "",
                "Operator-triggered request from the Activity tab.",
                f"Packet kind: {packet_kind}",
                f"Read mode: {audience_mode_label(self._current_audience_mode())}",
                f"Selected report: {report_title}",
                f"Report summary: {report_summary}",
                "",
                *quality_lines,
                "Source report body:",
                report_body,
                "",
                "Return a concise operator-facing summary with:",
                "1. Current blocker/risk state.",
                "2. Confidence level and why.",
                "3. The single best next typed action.",
                "",
                "Provenance: review-channel event packet posted by operator console.",
            ]
        )

    def _live_summary_packet_kind(self, report_id: str) -> str:
        """Choose review-channel packet kind for the selected Activity report."""
        if report_id == "quality":
            return "finding"
        return "draft"

    def _quality_backlog_live_lines(self, quality_backlog: object) -> list[str]:
        """Render compact quality-backlog facts for finding packets."""
        critical_paths = getattr(quality_backlog, "critical_paths", 0)
        high_paths = getattr(quality_backlog, "high_paths", 0)
        guard_failures = getattr(quality_backlog, "guard_failures", 0)
        lines = [
            "Live quality backlog context:",
            (
                f"- guard_failures={guard_failures} critical={critical_paths} "
                f"high={high_paths}"
            ),
        ]
        priorities = getattr(quality_backlog, "top_priorities", ())
        for row in list(priorities)[:3]:
            severity = getattr(row, "severity", "unknown")
            path = getattr(row, "path", "(unknown)")
            score = getattr(row, "score", 0)
            lines.append(f"- [{severity}] {path} score={score}")
        lines.append("")
        return lines

    def _current_report_id(self) -> str:
        report_id = self.activity_workspace.report_selector.currentData()
        if isinstance(report_id, str) and report_id:
            return report_id
        return "overview"

    def _current_audience_mode(self) -> str:
        return resolve_audience_mode(getattr(self, "_audience_mode", "simple"))

    def _current_summary_provider_id(self) -> str:
        provider_id = self.activity_workspace.assist_provider_selector.currentData()
        if isinstance(provider_id, str) and provider_id:
            return provider_id
        return "codex"

    def _live_summary_completion_message(
        self,
        *,
        target_agent: str,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> tuple[bool, str]:
        stripped_stdout = stdout.strip()
        if stripped_stdout:
            try:
                report = parse_review_channel_report(stripped_stdout)
            except ValueError:
                detail = self._first_visible_line(stderr)
                if detail:
                    return False, detail
                return False, "Live summary post did not return a readable status report."
            return evaluate_review_channel_post(
                report,
                target_agent=target_agent,
            )
        detail = self._first_visible_line(stderr)
        if detail:
            return False, detail
        fallback = (
            f"Live summary post to {target_agent} failed."
            if exit_code
            else f"Live summary post to {target_agent} completed."
        )
        return exit_code == 0, fallback
