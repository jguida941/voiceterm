"""Data refresh, approval queue, and command execution for the Operator Console.

Provides mixin methods that OperatorConsoleWindow inherits to handle
snapshot polling, approval decisions, and subprocess management.
"""

from __future__ import annotations

import traceback
from typing import Callable, Mapping

from ..state.activity_assist import build_summary_draft
from ..state.analytics_snapshot import collect_repo_analytics
from ..state.activity_reports import build_activity_report, recommended_next_step
from ..state.job_manager import JobManager, JobStatus
from ..state.repo_state import build_repo_state
from ..state.command_builder import (
    build_launch_command,
    build_process_audit_command,
    build_status_command,
    build_triage_command,
    build_rollover_command,
    render_command,
    evaluate_start_swarm_launch,
    evaluate_start_swarm_preflight,
    parse_review_channel_report,
)
from ..state.models import (
    AgentLaneData,
    ApprovalRequest,
    OperatorConsoleSnapshot,
)
from ..state.operator_decisions import record_operator_decision
from ..state.phone_status_snapshot import load_phone_control_snapshot
from ..state.presentation_state import (
    AnalyticsViewState,
    build_analytics_view_state,
    build_status_bar_text,
    build_system_banner_state,
    snapshot_digest,
)
from ..state.readability import audience_mode_label, resolve_audience_mode
from ..state.snapshot_builder import build_operator_console_snapshot
from ..theme import resolve_theme
from .ui_layouts import resolve_layout
from .widgets import KeyValuePanel, StatusIndicator

try:
    from PyQt6.QtCore import QProcess
    from PyQt6.QtWidgets import QApplication, QLabel

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False


class RefreshMixin:
    """Data refresh and command execution mixed into OperatorConsoleWindow."""

    def _resolve_operator_decision_approval(
        self,
        approval: ApprovalRequest | None,
    ) -> ApprovalRequest | None:
        """Return the explicit or selected approval packet, else emit the skip path."""
        if approval is not None:
            return approval
        approval = self.approval_panel.selected_approval()
        if approval is not None:
            return approval
        self._append_output("No approval packet selected.\n")
        self._record_event(
            "WARNING",
            "operator_decision_skipped",
            "Operator attempted a decision without a selected packet",
        )
        return None

    def request_manual_refresh(self) -> None:
        """Handle an operator-triggered refresh with visible feedback."""
        self._record_event(
            "INFO",
            "manual_refresh",
            "Operator requested a manual snapshot refresh",
            details={"layout_mode": getattr(self, "_layout_mode", None)},
        )
        self.refresh_snapshot()

    def refresh_snapshot(self) -> None:
        try:
            self._refresh_snapshot_once()
        except Exception as exc:  # broad-except: allow reason=desktop refresh loop must convert unexpected failures into visible diagnostics
            error_message = f"{type(exc).__name__}: {exc}"
            self._record_event(
                "ERROR",
                "refresh_failed",
                "Operator Console snapshot refresh failed",
                details={
                    "error": error_message,
                    "layout_mode": getattr(self, "_layout_mode", None),
                },
            )
            self._append_dev_log(traceback.format_exc())
            self.statusBar().showMessage(f"Refresh failed: {error_message}")

    def _refresh_snapshot_once(self) -> None:
        snapshot = build_operator_console_snapshot(self.repo_root)
        repo_analytics = collect_repo_analytics(self.repo_root)
        phone_snapshot = load_phone_control_snapshot(self.repo_root)
        repo_state = build_repo_state(self.repo_root)
        analytics_view = build_analytics_view_state(
            snapshot,
            repo_analytics=repo_analytics,
            phone_snapshot=phone_snapshot,
        )
        self._last_snapshot = snapshot
        self._last_analytics_view = analytics_view
        self._last_repo_state = repo_state

        self._update_lane_panel(self.codex_panel, self.codex_dot, snapshot.codex_lane)
        self._update_lane_panel(self.claude_panel, self.claude_dot, snapshot.claude_lane)
        self._update_lane_panel(
            self.operator_panel, self.operator_dot, snapshot.operator_lane
        )

        from .ui_scroll import replace_plain_text_preserving_scroll

        replace_plain_text_preserving_scroll(
            self.codex_session_text,
            snapshot.codex_session_text,
        )
        replace_plain_text_preserving_scroll(
            self.claude_session_text,
            snapshot.claude_session_text,
        )
        replace_plain_text_preserving_scroll(
            self.raw_bridge_text,
            snapshot.raw_bridge_text or "(bridge file missing)",
        )
        self._update_home_page(snapshot, analytics_view)
        self._update_activity_report(snapshot)
        self._update_activity_cards(snapshot)
        self._update_analytics_view(analytics_view)
        self._populate_approvals(snapshot.pending_approvals)

        pending_count = len(snapshot.pending_approvals)
        if pending_count > 0:
            self.operator_dot.set_level("warning")

        self._update_status_message(snapshot, repo_state=repo_state)

        new_digest = snapshot_digest(snapshot)
        if new_digest != self._last_snapshot_digest:
            self._record_event(
                "WARNING" if snapshot.warnings else "INFO",
                "snapshot_change",
                "Operator Console snapshot changed",
                details={
                    "pending_approvals": len(snapshot.pending_approvals),
                    "last_codex_poll": snapshot.last_codex_poll,
                    "last_worktree_hash": snapshot.last_worktree_hash,
                    "review_state_path": snapshot.review_state_path,
                    "warnings": list(snapshot.warnings),
                    "repo_branch": repo_state.branch,
                    "repo_head_short": repo_state.head_short,
                    "repo_dirty": repo_state.is_dirty,
                    "repo_dirty_files": repo_state.dirty_file_count,
                    "repo_risk": repo_state.risk_summary,
                },
            )
            self._last_snapshot_digest = new_digest

    def _update_lane_panel(
        self,
        panel: KeyValuePanel,
        toolbar_dot: StatusIndicator,
        lane: AgentLaneData | None,
    ) -> None:
        """Push structured lane data into the KV panel, dots, and card header."""
        if lane is None:
            return
        panel.set_title(lane.lane_title)
        panel.set_status(lane.status_hint)
        panel.set_rows(list(lane.rows))
        panel.set_raw_text(lane.raw_text)
        toolbar_dot.set_level(lane.status_hint)

        # Update the lane dot (card header dot, separate from toolbar dot)
        lane_dot = None
        if panel is self.codex_panel:
            lane_dot = getattr(self, "_codex_lane_dot", None)
        elif panel is self.claude_panel:
            lane_dot = getattr(self, "_claude_lane_dot", None)
        elif panel is self.operator_panel:
            lane_dot = getattr(self, "_operator_lane_dot", None)
        if lane_dot is not None:
            lane_dot.set_level(lane.status_hint)

        # Update card header labels dynamically from lane data
        card_labels = getattr(self, "_lane_card_labels", {})
        pair = card_labels.get(id(panel))
        if pair is not None:
            name_label, role_label = pair
            name_label.setText(lane.provider_name)
            role_label.setText(f"— {lane.role_label}")

    def _update_activity_report(self, snapshot: OperatorConsoleSnapshot) -> None:
        """Build the selected human-readable Activity report from the snapshot."""
        from .ui_scroll import replace_plain_text_preserving_scroll

        self.activity_workspace.set_audience_mode(self._current_audience_mode())
        report = build_activity_report(
            snapshot,
            report_id=self._current_report_id(),
            audience_mode=self._current_audience_mode(),
        )
        replace_plain_text_preserving_scroll(
            self._activity_text,
            report.body,
        )
        self._activity_meta_label.setText(
            " | ".join(
                (
                    f"Read mode: {audience_mode_label(self._current_audience_mode())}",
                    *report.provenance,
                )
            )
        )

    def _update_home_page(
        self,
        snapshot: OperatorConsoleSnapshot,
        analytics_view: AnalyticsViewState,
    ) -> None:
        """Refresh the start/home workspace from the current snapshot."""
        banner = build_system_banner_state(snapshot)
        report = build_activity_report(
            snapshot,
            report_id="overview",
            audience_mode=self._current_audience_mode(),
        )
        self.home_workspace.update_state(
            banner=banner,
            audience_mode=self._current_audience_mode(),
            audience_mode_label=audience_mode_label(self._current_audience_mode()),
            overview_summary=report.summary,
            overview_body=report.body,
            repo_summary=analytics_view.repo_text,
            quality_summary=analytics_view.quality_text,
            phone_summary=analytics_view.phone_text,
            next_step=recommended_next_step(snapshot),
        )

    def _update_status_message(
        self,
        snapshot: OperatorConsoleSnapshot,
        repo_state: object | None = None,
    ) -> None:
        """Refresh the footer text in the currently selected audience mode."""
        from ..state.repo_state import RepoStateSnapshot as _RS

        rs = repo_state if isinstance(repo_state, _RS) else None
        self.statusBar().showMessage(
            build_status_bar_text(
                snapshot,
                audience_mode=self._current_audience_mode(),
                repo_state=rs,
            )
        )

    def _update_activity_cards(self, snapshot: OperatorConsoleSnapshot) -> None:
        """Refresh the card-based agent summary strip on the Activity page."""
        self._update_activity_card(
            self.codex_activity_card,
            snapshot.codex_lane,
            fallback_name="Codex",
            fallback_role="Reviewer",
        )
        self._update_activity_card(
            self.workbench_codex_card,
            snapshot.codex_lane,
            fallback_name="Codex",
            fallback_role="Reviewer",
        )
        self._update_activity_card(
            self.claude_activity_card,
            snapshot.claude_lane,
            fallback_name="Claude",
            fallback_role="Implementer",
        )
        self._update_activity_card(
            self.workbench_claude_card,
            snapshot.claude_lane,
            fallback_name="Claude",
            fallback_role="Implementer",
        )
        self._update_activity_card(
            self.operator_activity_card,
            snapshot.operator_lane,
            fallback_name="Operator",
            fallback_role="Bridge State",
        )
        self._update_activity_card(
            self.workbench_operator_card,
            snapshot.operator_lane,
            fallback_name="Operator",
            fallback_role="Bridge State",
        )

    def _update_activity_card(
        self,
        card: object,
        lane: AgentLaneData | None,
        *,
        fallback_name: str,
        fallback_role: str,
    ) -> None:
        if lane is None:
            card.set_identity(
                agent_name=fallback_name,
                role=fallback_role,
                lane_title=f"{fallback_name} lane",
            )
            card.update_card(
                status_level="idle",
                status_text="No data",
                detail_text="No bridge-derived lane state is available yet.",
            )
            return

        card.set_identity(
            agent_name=lane.provider_name,
            role=lane.role_label,
            lane_title=lane.lane_title,
        )
        card.update_card(
            status_level=lane.status_hint,
            status_text=lane.state_label,
            detail_text=self._activity_card_detail(lane),
        )

    def _activity_card_detail(self, lane: AgentLaneData) -> str:
        details: list[str] = []
        for key, value in lane.rows:
            clean = " ".join(value.split())
            if not clean or clean in {"(missing)", "(unknown)"}:
                continue
            if key == "Approvals" and clean == "0":
                continue
            details.append(f"{key}: {clean[:72]}")
            if len(details) >= 2:
                break

        if lane.risk_label:
            details.append(f"Risk: {lane.risk_label}")
        if lane.confidence_label:
            details.append(f"Confidence: {lane.confidence_label}")

        return " | ".join(details) or "Waiting for bridge-derived activity."

    def _update_analytics_view(self, view_state: AnalyticsViewState) -> None:
        """Refresh the analytics dashboard text and KPI cards."""
        from .ui_scroll import replace_plain_text_preserving_scroll

        replace_plain_text_preserving_scroll(self._analytics_text, view_state.text)
        replace_plain_text_preserving_scroll(
            self._analytics_repo_text,
            view_state.repo_text,
        )
        replace_plain_text_preserving_scroll(
            self._analytics_quality_text,
            view_state.quality_text,
        )
        replace_plain_text_preserving_scroll(
            self._analytics_phone_text,
            view_state.phone_text,
        )

        # Update KPI cards if they exist
        kpi_cards = getattr(self, "_kpi_cards", None)
        if kpi_cards:
            for metric_id, value in view_state.kpi_values.items():
                rendered_value = value
                if metric_id in {"ci_runs", "mutation_score"} and value == "\u2014":
                    rendered_value = "n/a"
                self._set_kpi_value(kpi_cards, metric_id, rendered_value)

    def _set_kpi_value(
        self,
        kpi_cards: dict[str, object],
        metric_id: str,
        value: str,
    ) -> None:
        """Update a single KPI card's value label."""
        card = kpi_cards.get(metric_id)
        if card is None:
            return
        try:
            value_label = card.findChild(QLabel, "KPIValue")
        except RuntimeError:
            kpi_cards.pop(metric_id, None)
            return
        if value_label is not None:
            try:
                value_label.setText(value)
            except RuntimeError:
                kpi_cards.pop(metric_id, None)

    def _apply_theme(self, theme_id: str) -> None:
        resolved = resolve_theme(theme_id)
        self._theme_engine.apply_builtin_theme(resolved.theme_id)
        self._theme_engine.save_current()

    def _sync_theme_combo_selection(self) -> None:
        combo = getattr(self, "theme_combo", None)
        if combo is None:
            return

        active_selection = self._theme_engine.get_active_selection()
        combo.blockSignals(True)
        try:
            transient_index = combo.findData(self._dynamic_theme_combo_data)
            if transient_index >= 0:
                combo.removeItem(transient_index)

            if active_selection.theme_id is None:
                prefix = "Draft" if active_selection.kind == "draft" else "Active"
                combo.addItem(
                    f"{prefix}: {active_selection.display_name}",
                    self._dynamic_theme_combo_data,
                )
                combo.setCurrentIndex(combo.count() - 1)
                return

            theme_index = combo.findData(active_selection.theme_id)
            if theme_index >= 0:
                combo.setCurrentIndex(theme_index)
        finally:
            combo.blockSignals(False)

    def _sync_theme_from_engine(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(self._theme_engine.generate_stylesheet())
        self.theme_id = self._theme_engine.current_theme_id
        self._sync_theme_combo_selection()

    def _current_theme_colors(self) -> dict[str, str]:
        return self._theme_engine.get_colors()

    def _change_theme(self) -> None:
        theme_id = self.theme_combo.currentData()
        if not isinstance(theme_id, str):
            return
        if theme_id == self._dynamic_theme_combo_data:
            return
        if theme_id == self.theme_id:
            return
        self._apply_theme(theme_id)
        self._record_event(
            "INFO",
            "theme_changed",
            "Operator Console theme changed",
            details={"theme_id": theme_id},
        )
        self.statusBar().showMessage(
            f"Theme changed to {resolve_theme(theme_id).display_name}"
        )

    def _change_layout(self) -> None:
        mode_id = self.layout_combo.currentData()
        if not isinstance(mode_id, str):
            return
        if mode_id == self._layout_mode:
            return
        self._switch_layout(mode_id)
        self._record_event(
            "INFO",
            "layout_changed",
            "Operator Console layout changed",
            details={"layout_mode": mode_id},
        )
        desc = resolve_layout(mode_id)
        self.statusBar().showMessage(f"Layout changed to {desc.display_name}")
        self.refresh_snapshot()

    def _change_audience_mode(self) -> None:
        mode_id = self.read_mode_combo.currentData()
        if not isinstance(mode_id, str):
            return
        resolved = resolve_audience_mode(mode_id)
        if resolved == self._audience_mode:
            return
        self._audience_mode = resolved
        self._record_event(
            "INFO",
            "audience_mode_changed",
            "Operator Console readability mode changed",
            details={"audience_mode": resolved},
        )
        snapshot = getattr(self, "_last_snapshot", None)
        analytics_view = getattr(self, "_last_analytics_view", None)
        if snapshot is not None:
            if analytics_view is None:
                analytics_view = AnalyticsViewState(
                    text="",
                    repo_text="",
                    quality_text="",
                    phone_text="",
                    kpi_values={},
                )
            self._update_home_page(snapshot, analytics_view)
            self._update_activity_report(snapshot)
            self._update_status_message(
                snapshot, repo_state=getattr(self, "_last_repo_state", None)
            )
        else:
            self.home_workspace.set_audience_mode(resolved)
            self.activity_workspace.set_audience_mode(resolved)
            self.statusBar().showMessage(
                f"Read mode changed to {audience_mode_label(resolved)}."
            )

    # ── Agent detail ─────────────────────────────────────────────

    def _show_agent_detail(self, agent_id: str) -> None:
        """Open a detail dialog for the specified agent lane."""
        snapshot = getattr(self, "_last_snapshot", None)
        if snapshot is None:
            return
        lane = {
            "codex": snapshot.codex_lane,
            "claude": snapshot.claude_lane,
            "operator": snapshot.operator_lane,
        }.get(agent_id)
        if lane is None:
            return
        from .agent_detail import AgentDetailDialog

        dialog = AgentDetailDialog(
            lane,
            theme_colors=self._current_theme_colors(),
            parent=self,
        )
        dialog.exec()

    # ── Approval queue ───────────────────────────────────────────

    def _populate_approvals(self, approvals: tuple[ApprovalRequest, ...]) -> None:
        self.approval_panel.set_approvals(approvals)

    def record_decision(
        self,
        decision: str,
        *,
        selected_approval: ApprovalRequest | None = None,
        decision_note: str = "",
    ) -> None:
        approval = self._resolve_operator_decision_approval(selected_approval)
        if approval is None:
            return
        artifact = record_operator_decision(
            self.repo_root,
            approval=approval,
            decision=decision,
            note=decision_note,
        )
        self._append_output(
            f"Wrote operator {decision} artifacts:\n"
            f"- {artifact.json_path}\n"
            f"- {artifact.markdown_path}\n"
            f"- latest: {artifact.latest_json_path}\n"
        )
        self._record_event(
            "INFO",
            "operator_decision_recorded",
            "Recorded operator decision artifact",
            details={
                "decision": decision,
                "packet_id": approval.packet_id,
                "json_path": artifact.json_path,
                "markdown_path": artifact.markdown_path,
                "note_present": bool(decision_note.strip()),
            },
        )
        self.approval_panel.clear_note()

    # ── Command execution ────────────────────────────────────────

    def launch_dry_run(self) -> None:
        self._start_command(build_launch_command(live=False))

    def launch_live(self) -> None:
        if not self._live_terminal_supported:
            self._reject_live_terminal_action("Launch Live")
            return
        self._start_command(build_launch_command(live=True))

    def start_swarm(self) -> None:
        if not self._live_terminal_supported:
            self._reject_live_terminal_action(
                "Start Swarm",
                update_swarm_status=True,
            )
            return
        preflight_command = build_launch_command(live=False, output_format="json")
        if not self._start_command(
            preflight_command,
            context={"flow": "start_swarm", "step": "preflight"},
            busy_label="Swarm...",
        ):
            return
        detail = (
            "Running review-channel dry-run preflight. The live launch will start "
            "automatically if the preflight stays green."
        )
        self._set_start_swarm_status(
            swarm_level="warning",
            swarm_label="Swarm Preflight",
            swarm_detail=detail,
            command_preview=f"Preflight: {render_command(preflight_command)}",
        )
        self._append_output(
            "[Start Swarm] Dry-run preflight started. Live launch will follow automatically if it passes.\n"
        )
        self._record_event(
            "INFO",
            "start_swarm_requested",
            "Operator requested Start Swarm chained launch",
            details={"step": "preflight"},
        )

    def rollover_live(self) -> None:
        if not self._live_terminal_supported:
            self._reject_live_terminal_action("Rollover")
            return
        self._start_command(
            build_rollover_command(
                threshold_pct=self.threshold_spin.value(),
                await_ack_seconds=self.ack_wait_spin.value(),
                live=True,
            )
        )

    def show_ci_status(self) -> None:
        self._start_command(build_status_command(include_ci=True))

    def run_triage(self) -> None:
        self._start_command(build_triage_command(include_ci=True))

    def run_process_audit(self) -> None:
        self._start_command(build_process_audit_command(strict=True))

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

    def _set_start_swarm_status(
        self,
        *,
        swarm_level: str,
        swarm_label: str,
        swarm_detail: str,
        command_preview: str | None = None,
    ) -> None:
        """Mirror Start Swarm state across the visible command surfaces."""
        self.home_workspace.set_start_swarm_status(
            level=swarm_level,
            label=swarm_label,
            detail=swarm_detail,
            command_preview=command_preview,
        )
        self.activity_workspace.set_start_swarm_status(
            status_level=swarm_level,
            status_label=swarm_label,
            detail=swarm_detail,
            command_preview=command_preview,
        )

    def _reject_live_terminal_action(
        self,
        action_label: str,
        *,
        update_swarm_status: bool = False,
    ) -> None:
        """Fail closed when Terminal.app-backed live controls are unavailable."""
        message = self._live_terminal_support_detail
        if action_label == "Start Swarm":
            message += " Use Launch Dry Run to execute the repo-visible preflight only."
        self._append_output(f"[{action_label}] {message}\n")
        self._reveal_output_surface("command_output")
        self._record_event(
            "WARNING",
            "live_terminal_gated",
            f"{action_label} blocked because Terminal.app live launch is unavailable",
            details={"action": action_label},
        )
        self.statusBar().showMessage(message)
        if update_swarm_status:
            self._set_start_swarm_status(
                swarm_level="stale",
                swarm_label="Swarm Live-Gated",
                swarm_detail=message,
                command_preview=(
                    "Use Launch Dry Run to execute the review-channel preflight "
                    "without opening Terminal.app sessions."
                ),
            )

    def _start_command(
        self,
        command: list[str],
        *,
        context: dict[str, object] | None = None,
        busy_label: str | None = None,
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
        process.finished.connect(self._on_process_finished)
        self._process = process
        self._active_command_context = dict(context or {})
        self._active_command_stdout = ""
        self._active_command_stderr = ""
        process.start()
        return True

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

    def _resolve_start_swarm_result(
        self,
        *,
        exit_code: int,
        stdout: str,
        stderr: str,
        evaluator: Callable[[Mapping[str, object]], tuple[bool, str]],
        invalid_json_message: str,
        empty_output_message: str,
    ) -> tuple[bool, str]:
        stripped_stdout = stdout.strip()
        if stripped_stdout:
            try:
                report = parse_review_channel_report(stripped_stdout)
            except ValueError:
                detail = self._first_visible_line(stderr) or invalid_json_message
                return False, detail
            return evaluator(report)
        detail = self._first_visible_line(stderr)
        if detail:
            return False, detail
        if exit_code:
            return False, empty_output_message
        return False, invalid_json_message

    def _handle_start_swarm_completion(
        self,
        *,
        step: str,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> bool:
        if step == "preflight":
            ok, message = self._resolve_start_swarm_result(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                evaluator=evaluate_start_swarm_preflight,
                invalid_json_message=(
                    "Start Swarm preflight failed: review-channel did not return a JSON status report."
                ),
                empty_output_message=(
                    "Start Swarm preflight failed without a readable status payload."
                ),
            )
            if not ok:
                self._set_start_swarm_status(
                    swarm_level="stale",
                    swarm_label="Swarm Blocked",
                    swarm_detail=message,
                    command_preview=(
                        "Last command: "
                        + render_command(
                            build_launch_command(live=False, output_format="json")
                        )
                    ),
                )
                self._append_output(f"[Start Swarm] {message}\n")
                self._record_event(
                    "WARNING" if exit_code == 0 else "ERROR",
                    "start_swarm_preflight_failed",
                    "Start Swarm preflight blocked live launch",
                    details={"exit_code": exit_code, "message": message},
                )
                return False

            launch_detail = f"{message} Launching live review-channel sessions."
            live_command = build_launch_command(live=True, output_format="json")
            if not self._live_terminal_supported:
                self._set_start_swarm_status(
                    swarm_level="stale",
                    swarm_label="Swarm Live-Gated",
                    swarm_detail=self._live_terminal_support_detail,
                    command_preview=(
                        "Use Launch Dry Run to execute the review-channel preflight "
                        "without opening Terminal.app sessions."
                    ),
                )
                self._append_output(f"[Start Swarm] {self._live_terminal_support_detail}\n")
                self._record_event(
                    "WARNING",
                    "start_swarm_live_gated",
                    "Start Swarm preflight passed but live launch is Terminal.app-gated",
                    details={"message": self._live_terminal_support_detail},
                )
                return False
            self._set_start_swarm_status(
                swarm_level="warning",
                swarm_label="Swarm Launching",
                swarm_detail=launch_detail,
                command_preview=f"Live launch: {render_command(live_command)}",
            )
            self._append_output(f"[Start Swarm] {message}\n")
            self._record_event(
                "INFO",
                "start_swarm_preflight_passed",
                "Start Swarm preflight passed; launching live swarm",
                details={"message": message},
            )
            if not self._start_command(
                live_command,
                context={"flow": "start_swarm", "step": "live"},
                busy_label="Swarm...",
            ):
                failure = (
                    "Start Swarm live launch could not begin because another command is already running."
                )
                self._set_start_swarm_status(
                    swarm_level="stale",
                    swarm_label="Swarm Failed",
                    swarm_detail=failure,
                    command_preview=f"Blocked live launch: {render_command(live_command)}",
                )
                self._append_output(f"[Start Swarm] {failure}\n")
                self._record_event(
                    "ERROR",
                    "start_swarm_live_launch_rejected",
                    "Start Swarm preflight passed but the live launch could not begin",
                    details={"message": failure},
                )
                return False
            return True

        if step == "live":
            ok, message = self._resolve_start_swarm_result(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                evaluator=evaluate_start_swarm_launch,
                invalid_json_message=(
                    "Start Swarm live launch failed: review-channel did not return a JSON status report."
                ),
                empty_output_message=(
                    "Start Swarm live launch failed without a readable status payload."
                ),
            )
            if ok:
                self._set_start_swarm_status(
                    swarm_level="active",
                    swarm_label="Swarm Running",
                    swarm_detail=message,
                    command_preview=(
                        "Last command: "
                        + render_command(
                            build_launch_command(live=True, output_format="json")
                        )
                    ),
                )
                self._record_event(
                    "INFO",
                    "start_swarm_live_ok",
                    "Start Swarm live launch reported success",
                    details={"message": message},
                )
            else:
                self._set_start_swarm_status(
                    swarm_level="stale",
                    swarm_label="Swarm Failed",
                    swarm_detail=message,
                    command_preview=(
                        "Last command: "
                        + render_command(
                            build_launch_command(live=True, output_format="json")
                        )
                    ),
                )
                self._record_event(
                    "ERROR" if exit_code else "WARNING",
                    "start_swarm_live_failed",
                    "Start Swarm live launch reported failure",
                    details={"exit_code": exit_code, "message": message},
                )
            self._append_output(f"[Start Swarm] {message}\n")
        return False

    def _on_process_finished(self, exit_code: int, _exit_status: object) -> None:
        active_context = self._active_command_context or {}
        stdout = self._active_command_stdout
        stderr = self._active_command_stderr

        self._append_output(f"\n[process exited with code {exit_code}]\n")
        self._record_event(
            "ERROR" if exit_code else "INFO",
            "command_finished",
            "Operator Console command finished",
            details={"exit_code": exit_code, "context": active_context},
        )
        self._process = None
        self._active_command_context = None
        self._active_command_stdout = ""
        self._active_command_stderr = ""

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
            return

        self._set_command_controls_busy(False)
        self.statusBar().showMessage(f"Command finished with exit code {exit_code}.")
        self._process = None
        self.refresh_snapshot()

    def _describe_command(self, command: list[str]) -> str:
        """Return a short operator-facing label for a command."""
        if "process-audit" in command:
            return "Process Audit"
        if "triage" in command:
            return "Triage"
        if "status" in command:
            return "CI Status"
        if "rollover" in command:
            return "Rollover"
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
