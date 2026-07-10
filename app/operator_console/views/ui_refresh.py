"""Data refresh, approval queue, and command execution for the Operator Console.

Provides mixin methods that OperatorConsoleWindow inherits to handle
snapshot polling, approval decisions, and subprocess management.
"""

from __future__ import annotations

import traceback

from pathlib import Path

from ..state.snapshots.analytics_snapshot import collect_repo_analytics
from ..state.activity.activity_reports import build_activity_report, recommended_next_step
from ..collaboration.conversation_state import build_conversation_snapshot
from ..state.jobs.job_manager import JobManager, JobStatus
from ..state.repo.repo_state import build_repo_state
from ..state.core.models import (
    AgentLaneData,
    ApprovalRequest,
    OperatorConsoleSnapshot,
)
from ..state.review.operator_decisions import record_operator_decision
from ..state.snapshots.phone_status_snapshot import load_phone_control_snapshot
from ..state.snapshots.ralph_guardrail_snapshot import load_ralph_guardrail_snapshot
from ..state.presentation.presentation_state import (
    AnalyticsViewState,
    build_analytics_view_state,
    build_status_bar_text,
    build_system_banner_state,
    snapshot_digest,
)
from ..state.core.readability import audience_mode_label, resolve_audience_mode
from ..state.snapshots.snapshot_builder import build_operator_console_snapshot
from ..collaboration.task_board_state import build_task_board_snapshot
from ..collaboration.timeline_builder import build_timeline_from_snapshot
from ..workflows.workflow_surface_state import build_workflow_surface_state
from ..theme import resolve_theme
from .layout.ui_layouts import resolve_layout
from .shared.widgets import KeyValuePanel, StatusIndicator

try:
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
        except Exception as exc:  # broad-except: allow reason=desktop refresh loop must convert unexpected failures into visible diagnostics fallback=record error, append dev log, and keep UI running
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
        ralph_snapshot = load_ralph_guardrail_snapshot(self.repo_root)
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
        self._update_lane_panel(self.cursor_panel, self.cursor_dot, snapshot.cursor_lane)
        self._update_lane_panel(
            self.operator_panel, self.operator_dot, snapshot.operator_lane
        )

        from .shared.ui_scroll import replace_plain_text_preserving_scroll

        session_panels = (
            (self.codex_session_text, snapshot.codex_session_text),
            (self.codex_session_stats_text, snapshot.codex_session_stats_text),
            (self.codex_session_registry_text, snapshot.codex_session_registry_text),
            (self.claude_session_text, snapshot.claude_session_text),
            (self.claude_session_stats_text, snapshot.claude_session_stats_text),
            (self.claude_session_registry_text, snapshot.claude_session_registry_text),
            (self.cursor_session_text, snapshot.cursor_session_text),
            (self.cursor_session_stats_text, snapshot.cursor_session_stats_text),
            (self.cursor_session_registry_text, snapshot.cursor_session_registry_text),
            (self.raw_bridge_text, snapshot.raw_bridge_text or "(bridge file missing)"),
        )
        for widget, content in session_panels:
            replace_plain_text_preserving_scroll(widget, content)
        self._update_home_page(snapshot, analytics_view)
        self._update_activity_report(snapshot)
        self._update_activity_cards(snapshot)
        self._update_analytics_view(analytics_view)
        self._populate_approvals(snapshot.pending_approvals)
        self.timeline_panel.set_events(
            build_timeline_from_snapshot(snapshot, repo_root=self.repo_root)
        )
        workflow_state = build_workflow_surface_state(
            snapshot,
            repo_state=repo_state,
            workflow_preset_id=self._workflow_preset_id,
            swarm_health_label=self.home_workspace.start_swarm_label.text(),
        )
        self.workflow_header_bar.set_state(workflow_state)
        self.workflow_timeline_footer.set_state(workflow_state)

        # Refresh Ralph guardrail dashboard if present
        ralph_dashboard = getattr(self, "ralph_dashboard", None)
        if ralph_dashboard is not None:
            ralph_dashboard.set_snapshot(ralph_snapshot)

        # Refresh team collaboration panels from the same review-state data
        review_path = (
            Path(snapshot.review_state_path)
            if snapshot.review_state_path
            else None
        )
        conversation_snap = build_conversation_snapshot(
            review_state_path=review_path,
        )
        self.conversation_panel.set_conversation(conversation_snap)
        task_board_snap = build_task_board_snapshot(
            review_state_path=review_path,
        )
        self.task_board_panel.set_board(task_board_snap)

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
        elif panel is self.cursor_panel:
            lane_dot = getattr(self, "_cursor_lane_dot", None)
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
        from .shared.ui_scroll import replace_plain_text_preserving_scroll

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
        from ..state.repo.repo_state import RepoStateSnapshot as _RS

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
        if hasattr(self, "cursor_activity_card"):
            self._update_activity_card(
                self.cursor_activity_card,
                snapshot.cursor_lane,
                fallback_name="Cursor",
                fallback_role="Editor",
            )
        self._update_activity_card(
            self.workbench_operator_card,
            snapshot.operator_lane,
            fallback_name="Operator",
            fallback_role="Bridge State",
        )
        if hasattr(self, "workbench_cursor_card"):
            self._update_activity_card(
                self.workbench_cursor_card,
                snapshot.cursor_lane,
                fallback_name="Cursor",
                fallback_role="Editor",
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
        from .shared.ui_scroll import replace_plain_text_preserving_scroll

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
        self._persist_layout_state()
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
            "cursor": snapshot.cursor_lane,
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
