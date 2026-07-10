"""Tests for UI layout correctness: nav tabs, monitor tabs, approval queue,
lane structure, activity page, and responsive sizing."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtCore import QProcess
    from PyQt6.QtWidgets import QApplication

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QApplication = None
    QProcess = None


def _blank_snapshot():
    from app.operator_console.state.core.models import OperatorConsoleSnapshot

    return OperatorConsoleSnapshot(
        codex_panel_text="",
        claude_panel_text="",
        operator_panel_text="",
        codex_session_text="",
        claude_session_text="",
        raw_bridge_text="",
        review_mode=None,
        last_codex_poll=None,
        last_worktree_hash=None,
        pending_approvals=(),
        warnings=(),
        review_state_path=None,
        codex_lane=None,
        claude_lane=None,
        operator_lane=None,
    )


def _make_window(
    *,
    theme_id: str | None = "codex",
    engine: object | None = None,
    layout_mode: str = "tabbed",
    repo: Path | None = None,
    persist_layout_state: bool = False,
):
    """Build an OperatorConsoleWindow with mocked dependencies."""
    from app.operator_console.logging_support import OperatorConsoleDiagnostics
    from app.operator_console.theme.runtime.theme_engine import ThemeEngine
    from app.operator_console.views.main_window import OperatorConsoleWindow

    diag = MagicMock(spec=OperatorConsoleDiagnostics)
    diag.destination_summary = "mock"
    diag.log = MagicMock(return_value="mock log line")

    repo = repo or Path("/tmp/mock-repo")
    with patch(
        "app.operator_console.views.ui_refresh.build_operator_console_snapshot"
    ) as mock_snap, patch(
        "app.operator_console.views.main_window.get_engine"
    ) as mock_get_engine:
        mock_snap.return_value = _blank_snapshot()
        engine = engine or ThemeEngine()
        engine.save_current = MagicMock()
        mock_get_engine.return_value = engine
        window = OperatorConsoleWindow(
            repo,
            diagnostics=diag,
            dev_log_enabled=False,
            theme_id=theme_id,
            layout_mode=layout_mode,
            persist_layout_state=persist_layout_state,
        )
    return window


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class NavTabsTests(unittest.TestCase):
    """Top-level navigation: Home | Dashboard | Monitor | Activity."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_nav_tabs_has_five_pages(self) -> None:
        window = _make_window()
        self.assertEqual(window._nav_tabs.count(), 5)

    def test_nav_tab_labels(self) -> None:
        window = _make_window()
        labels = [
            window._nav_tabs.tabText(i) for i in range(window._nav_tabs.count())
        ]
        self.assertEqual(labels, ["Home", "Dashboard", "Monitor", "Activity", "Collaborate"])

    def test_nav_tab_bar_is_not_expanding(self) -> None:
        """Nav tabs use pill-style, not full-width expanding."""
        window = _make_window()
        self.assertFalse(window._nav_tabs.tabBar().expanding())

    def test_nav_tab_bar_has_object_name(self) -> None:
        window = _make_window()
        self.assertEqual(window._nav_tabs.tabBar().objectName(), "NavTabBar")

    def test_home_is_default_page(self) -> None:
        window = _make_window()
        self.assertEqual(window._nav_tabs.currentIndex(), 0)

    def test_home_workspace_exists(self) -> None:
        window = _make_window()
        self.assertIsNotNone(window.home_workspace)

    def test_home_exposes_visible_workflow_launchpad(self) -> None:
        window = _make_window()
        self.assertIsNotNone(window.home_workspace.workflow_launchpad)
        self.assertIsNotNone(window.home_workspace.start_swarm_button.parent())
        self.assertGreater(window.home_workspace.workflow_selector.count(), 0)

    def test_home_dashboard_button_navigation_works(self) -> None:
        window = _make_window()
        window._open_dashboard_surface()
        self.assertEqual(window._nav_tabs.currentIndex(), 1)


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class MonitorTabsTests(unittest.TestCase):
    """Monitor page sub-tabs: sessions plus raw bridge and logs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_monitor_tabs_has_six_panels(self) -> None:
        window = _make_window()
        self.assertEqual(window._monitor_tabs.count(), 6)

    def test_monitor_tab_bar_is_expanding(self) -> None:
        window = _make_window()
        self.assertTrue(window._monitor_tabs.tabBar().expanding())

    def test_monitor_tab_labels_are_clean(self) -> None:
        window = _make_window()
        tab_bar = window._monitor_tabs.tabBar()
        for i in range(tab_bar.count()):
            label = tab_bar.tabText(i)
            self.assertEqual(label, label.strip())

    def test_monitor_tab_labels_match_session_first_order(self) -> None:
        window = _make_window()
        labels = [
            window._monitor_tabs.tabText(i)
            for i in range(window._monitor_tabs.count())
        ]
        self.assertEqual(
            labels,
            [
                "Codex Session",
                "Claude Session",
                "Cursor Session",
                "Bridge",
                "Launcher Output",
                "Diagnostics",
            ],
        )

    def test_reveal_command_output_selects_monitor_output_tab(self) -> None:
        window = _make_window()
        window._reveal_output_surface("command_output")
        self.assertEqual(window._nav_tabs.currentIndex(), 2)
        self.assertEqual(window._monitor_tabs.currentIndex(), 4)

    def test_reveal_diagnostics_selects_monitor_diagnostics_tab(self) -> None:
        window = _make_window()
        window._reveal_output_surface("diagnostics")
        self.assertEqual(window._nav_tabs.currentIndex(), 2)
        self.assertEqual(window._monitor_tabs.currentIndex(), 5)

    def test_bridge_panel_wraps_lines_for_human_reading(self) -> None:
        window = _make_window()
        self.assertEqual(
            window.raw_bridge_text.lineWrapMode(),
            type(window.raw_bridge_text).LineWrapMode.WidgetWidth,
        )

    def test_command_output_keeps_no_wrap(self) -> None:
        window = _make_window()
        self.assertEqual(
            window.command_output.lineWrapMode(),
            type(window.command_output).LineWrapMode.NoWrap,
        )

    def test_session_panes_keep_no_wrap(self) -> None:
        window = _make_window()
        self.assertEqual(
            window.codex_session_text.lineWrapMode(),
            type(window.codex_session_text).LineWrapMode.NoWrap,
        )
        self.assertEqual(
            window.claude_session_text.lineWrapMode(),
            type(window.claude_session_text).LineWrapMode.NoWrap,
        )
        self.assertEqual(
            window.cursor_session_text.lineWrapMode(),
            type(window.cursor_session_text).LineWrapMode.NoWrap,
        )

    def test_session_support_panes_use_expected_wrap_modes(self) -> None:
        window = _make_window()
        self.assertEqual(
            window.codex_session_stats_text.lineWrapMode(),
            type(window.codex_session_stats_text).LineWrapMode.WidgetWidth,
        )
        self.assertEqual(
            window.claude_session_stats_text.lineWrapMode(),
            type(window.claude_session_stats_text).LineWrapMode.WidgetWidth,
        )
        self.assertEqual(
            window.cursor_session_stats_text.lineWrapMode(),
            type(window.cursor_session_stats_text).LineWrapMode.WidgetWidth,
        )
        self.assertEqual(
            window.codex_session_registry_text.lineWrapMode(),
            type(window.codex_session_registry_text).LineWrapMode.NoWrap,
        )
        self.assertEqual(
            window.claude_session_registry_text.lineWrapMode(),
            type(window.claude_session_registry_text).LineWrapMode.NoWrap,
        )
        self.assertEqual(
            window.cursor_session_registry_text.lineWrapMode(),
            type(window.cursor_session_registry_text).LineWrapMode.NoWrap,
        )

    def test_session_detail_cards_start_on_stats_face(self) -> None:
        window = _make_window()
        self.assertIsNotNone(window.codex_session_detail_card)
        self.assertIsNotNone(window.claude_session_detail_card)
        self.assertIsNotNone(window.cursor_session_detail_card)
        self.assertEqual(window.codex_session_detail_card.current_title, "Codex Stats")
        self.assertEqual(window.claude_session_detail_card.current_title, "Claude Stats")
        self.assertEqual(window.cursor_session_detail_card.current_title, "Cursor Stats")


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class ActivityPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_activity_text_widget_exists(self) -> None:
        window = _make_window()
        self.assertIsNotNone(getattr(window, "_activity_text", None))

    def test_activity_text_is_readonly(self) -> None:
        window = _make_window()
        self.assertTrue(window._activity_text.isReadOnly())

    def test_activity_workspace_exposes_summary_cards(self) -> None:
        window = _make_window()
        self.assertIsNotNone(window.activity_workspace)
        self.assertEqual(window.codex_activity_card.name_label.text(), "Codex")
        self.assertEqual(window.cursor_activity_card.name_label.text(), "Cursor")
        self.assertEqual(window.claude_activity_card.name_label.text(), "Claude")
        self.assertEqual(window.operator_activity_card.name_label.text(), "Operator")

    def test_activity_workspace_exposes_assist_panel(self) -> None:
        window = _make_window()
        self.assertTrue(window._assist_text.isReadOnly())
        self.assertIn("Draft from the selected report", window._assist_meta_label.text())

    def test_activity_workspace_exposes_report_selector(self) -> None:
        window = _make_window()
        self.assertGreater(window.activity_workspace.report_selector.count(), 0)
        self.assertIsNotNone(window._activity_meta_label)

    def test_activity_exposes_visible_workflow_launchpad(self) -> None:
        window = _make_window()
        self.assertIsNotNone(window.activity_workspace.workflow_launchpad)
        self.assertIsNotNone(
            window.activity_workspace.activity_start_swarm_button.parent()
        )
        self.assertGreater(window.activity_workspace.workflow_selector.count(), 0)

    def test_switching_to_technical_mode_refreshes_without_crash(self) -> None:
        from app.operator_console.state.core.models import (
            AgentLaneData,
            OperatorConsoleSnapshot,
        )
        from app.operator_console.state.presentation.presentation_state import AnalyticsViewState

        window = _make_window()
        window._last_snapshot = OperatorConsoleSnapshot(
            codex_panel_text="",
            claude_panel_text="",
            operator_panel_text="",
            codex_session_text="",
            claude_session_text="",
            raw_bridge_text="",
            review_mode="markdown-only",
            last_codex_poll="2026-03-08T20:00:00Z",
            last_worktree_hash="abc123",
            pending_approvals=(),
            warnings=(),
            review_state_path=None,
            codex_lane=AgentLaneData(
                provider_name="Codex",
                lane_title="Codex Bridge Monitor",
                role_label="Reviewer",
                status_hint="active",
                state_label="reviewing",
                rows=(("Poll", "active"),),
                raw_text="",
            ),
            claude_lane=None,
            operator_lane=None,
        )
        window._last_analytics_view = AnalyticsViewState(
            text="",
            repo_text="repo text",
            quality_text="quality text",
            phone_text="phone text",
            kpi_values={},
        )

        technical_index = window.read_mode_combo.findData("technical")
        window.read_mode_combo.setCurrentIndex(technical_index)
        window._change_audience_mode()

        self.assertEqual(window.home_workspace.mode_badge.text(), "Read: Technical")
        self.assertEqual(window.home_workspace.overview_title.text(), "Ops Digest")
        self.assertEqual(window.home_workspace.explainer_title.text(), "Repo Digest")
        self.assertEqual(window.activity_workspace.report_title_label.text(), "Report Digest")
        self.assertEqual(window.activity_workspace.actions_title_label.text(), "Operator Flow")
        self.assertTrue(bool(window.home_workspace.overview_body.property("digestMode")))
        self.assertIn("What is happening now:", window.home_workspace.overview_body.text())

    def test_refresh_selected_report_populates_human_summary(self) -> None:
        from app.operator_console.state.core.models import (
            AgentLaneData,
            OperatorConsoleSnapshot,
        )

        window = _make_window()
        snapshot = OperatorConsoleSnapshot(
            codex_panel_text="",
            claude_panel_text="",
            operator_panel_text="",
            codex_session_text="",
            claude_session_text="",
            raw_bridge_text="",
            review_mode="markdown-only",
            last_codex_poll="2026-03-08T20:00:00Z",
            last_worktree_hash="abc123",
            pending_approvals=(),
            warnings=(),
            review_state_path=None,
            codex_lane=AgentLaneData(
                provider_name="Codex",
                lane_title="Codex Bridge Monitor",
                role_label="Reviewer",
                status_hint="active",
                state_label="reviewing",
                rows=(("Poll", "active"),),
                raw_text="",
            ),
            claude_lane=None,
            operator_lane=None,
        )

        window._last_snapshot = snapshot
        index = window.activity_workspace.report_selector.findData("overview")
        window.activity_workspace.report_selector.setCurrentIndex(index)
        window.refresh_selected_report()

        self.assertIn("Recommended next step", window._activity_text.toPlainText())
        self.assertIn("Script-derived overview", window._activity_meta_label.text())

    def test_generate_summary_draft_populates_activity_panel(self) -> None:
        from app.operator_console.state.core.models import (
            AgentLaneData,
            OperatorConsoleSnapshot,
        )

        window = _make_window()
        snapshot = OperatorConsoleSnapshot(
            codex_panel_text="",
            claude_panel_text="",
            operator_panel_text="",
            codex_session_text="",
            claude_session_text="",
            raw_bridge_text="",
            review_mode="markdown-only",
            last_codex_poll="2026-03-08T20:00:00Z",
            last_worktree_hash="abc123",
            pending_approvals=(),
            warnings=(),
            review_state_path=None,
            codex_lane=AgentLaneData(
                provider_name="Codex",
                lane_title="Codex Bridge Monitor",
                role_label="Reviewer",
                status_hint="active",
                state_label="reviewing",
                rows=(("Poll", "active"),),
                raw_text="",
            ),
            claude_lane=None,
            operator_lane=None,
        )

        window._last_snapshot = snapshot
        report_index = window.activity_workspace.report_selector.findData("codex")
        provider_index = window.activity_workspace.assist_provider_selector.findData("claude")
        window.activity_workspace.report_selector.setCurrentIndex(report_index)
        window.activity_workspace.assist_provider_selector.setCurrentIndex(provider_index)
        window.generate_summary_draft()

        self.assertIn("Claude Draft", window._assist_text.toPlainText())
        self.assertIn("Selected report: Codex Report", window._assist_text.toPlainText())
        self.assertIn("Target provider: Claude Draft", window._assist_meta_label.text())


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class ThemeSelectionSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_toolbar_theme_selection_initializes_engine_state(self) -> None:
        window = _make_window()

        self.assertEqual(window.theme_combo.currentData(), "codex")
        self.assertEqual(window._theme_engine.current_theme_id, "codex")

    def test_editor_draft_selection_updates_toolbar_combo_label(self) -> None:
        window = _make_window()

        window._theme_engine.set_color("accent", "#123456")

        self.assertEqual(window.theme_combo.currentData(), window._dynamic_theme_combo_data)
        self.assertEqual(window.theme_combo.currentText(), "Draft: Custom")

    def test_window_preserves_engine_draft_when_no_startup_theme_is_requested(self) -> None:
        from app.operator_console.theme.runtime.theme_engine import ThemeEngine

        engine = ThemeEngine()
        engine.set_color("accent", "#123456")

        window = _make_window(theme_id=None, engine=engine)

        self.assertIsNone(window._theme_engine.current_theme_id)
        self.assertEqual(window.theme_combo.currentData(), window._dynamic_theme_combo_data)
        self.assertEqual(window.theme_combo.currentText(), "Draft: Custom")

    def test_toolbar_theme_change_persists_engine_state(self) -> None:
        window = _make_window()
        window._theme_engine.save_current = MagicMock()
        theme_index = window.theme_combo.findData("claude")
        window.theme_combo.setCurrentIndex(theme_index)

        window._change_theme()

        self.assertEqual(window._theme_engine.current_theme_id, "claude")
        window._theme_engine.save_current.assert_called_once_with()


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class ApprovalQueueVisibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_approval_container_shows_zero_state_when_empty(self) -> None:
        window = _make_window()
        self.assertFalse(window._approval_container.isHidden())
        self.assertEqual(window.approval_panel._count_badge.text(), "0")
        self.assertEqual(window.approval_panel._detail_header.text(), "0 Pending")

    def _make_approval(self, packet_id: str = "pkt-001") -> object:
        from app.operator_console.state.core.models import ApprovalRequest

        return ApprovalRequest(
            packet_id=packet_id,
            from_agent="codex",
            to_agent="operator",
            summary="Test approval",
            body="body text",
            policy_hint="auto",
            requested_action="merge",
            status="pending",
        )

    def test_approval_container_shows_when_items_present(self) -> None:
        window = _make_window()
        window._populate_approvals((self._make_approval(),))
        self.assertFalse(window._approval_container.isHidden())

    def test_approval_container_stays_visible_after_clear(self) -> None:
        window = _make_window()
        window._populate_approvals((self._make_approval(),))
        self.assertFalse(window._approval_container.isHidden())
        window._populate_approvals(())
        self.assertFalse(window._approval_container.isHidden())
        self.assertEqual(window.approval_panel._count_badge.text(), "0")
        self.assertEqual(window.approval_panel._detail_header.text(), "0 Pending")


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class LaneStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_lane_dots_are_stored(self) -> None:
        window = _make_window()
        self.assertIsNotNone(getattr(window, "_codex_lane_dot", None))
        self.assertIsNotNone(getattr(window, "_claude_lane_dot", None))
        self.assertIsNotNone(getattr(window, "_cursor_lane_dot", None))
        self.assertIsNotNone(getattr(window, "_operator_lane_dot", None))

    def test_toolbar_dots_are_separate_from_lane_dots(self) -> None:
        window = _make_window()
        self.assertIsNot(window.codex_dot, window._codex_lane_dot)
        self.assertIsNot(window.claude_dot, window._claude_lane_dot)
        self.assertIsNot(window.cursor_dot, window._cursor_lane_dot)
        self.assertIsNot(window.operator_dot, window._operator_lane_dot)

    def test_action_buttons_exist(self) -> None:
        """Action buttons should be created and accessible."""
        window = _make_window()
        self.assertIsNotNone(window.refresh_button)
        self.assertIsNotNone(window.launch_dry_button)
        self.assertIsNotNone(window.launch_live_button)
        self.assertIsNotNone(window.rollover_button)
        self.assertIsNotNone(window.home_workspace.start_swarm_button)
        self.assertIsNotNone(window.activity_workspace.activity_start_swarm_button)

    def test_busy_state_updates_action_buttons(self) -> None:
        window = _make_window()
        window._set_command_controls_busy(
            True,
            label="Loop...",
            busy_buttons=window._loop_action_buttons(),
        )
        self.assertFalse(window.launch_dry_button.isEnabled())
        self.assertFalse(window.launch_live_button.isEnabled())
        self.assertFalse(window.rollover_button.isEnabled())
        self.assertFalse(window.home_workspace.run_loop_button.isEnabled())
        self.assertFalse(window.activity_workspace.activity_run_loop_button.isEnabled())
        self.assertFalse(window.home_workspace.start_swarm_button.isEnabled())
        self.assertFalse(window.activity_workspace.activity_start_swarm_button.isEnabled())
        self.assertFalse(window.activity_workspace.activity_dry_run_button.isEnabled())
        self.assertFalse(window.activity_workspace.activity_ci_status_button.isEnabled())
        self.assertFalse(window.home_workspace.workflow_selector.isEnabled())
        self.assertFalse(window.activity_workspace.workflow_selector.isEnabled())
        self.assertEqual(window.launch_live_button.text(), "Live")
        self.assertEqual(window.home_workspace.run_loop_button.text(), "Loop...")
        self.assertEqual(window.activity_workspace.activity_run_loop_button.text(), "Loop...")

        window._set_command_controls_busy(False)
        self.assertTrue(window.launch_dry_button.isEnabled())
        self.assertTrue(window.launch_live_button.isEnabled())
        self.assertTrue(window.rollover_button.isEnabled())
        self.assertTrue(window.home_workspace.run_loop_button.isEnabled())
        self.assertTrue(window.activity_workspace.activity_run_loop_button.isEnabled())
        self.assertTrue(window.home_workspace.start_swarm_button.isEnabled())
        self.assertTrue(window.activity_workspace.activity_start_swarm_button.isEnabled())
        self.assertTrue(window.activity_workspace.activity_dry_run_button.isEnabled())
        self.assertTrue(window.activity_workspace.activity_ci_status_button.isEnabled())
        self.assertTrue(window.home_workspace.workflow_selector.isEnabled())
        self.assertTrue(window.activity_workspace.workflow_selector.isEnabled())
        self.assertEqual(window.launch_live_button.text(), "Live")
        self.assertEqual(window.home_workspace.run_loop_button.text(), "Run Loop")
        self.assertEqual(window.activity_workspace.activity_run_loop_button.text(), "Run Loop")
        self.assertEqual(window.home_workspace.start_swarm_button.text(), "Launch Review")
        self.assertEqual(
            window.activity_workspace.activity_start_swarm_button.text(),
            "Launch Review",
        )

    def test_start_swarm_uses_json_preflight_command(self) -> None:
        from app.operator_console.workflows import build_launch_command

        window = _make_window()
        window._apply_workflow_preset("continuous_swarm", announce=False)
        with patch.object(window, "_start_command", return_value=True) as mock_start:
            window.start_swarm()

        mock_start.assert_called_once_with(
            build_launch_command(
                live=False,
                output_format="json",
                refresh_bridge_heartbeat_if_stale=True,
                scope="dev/active/continuous_swarm.md",
                promotion_plan="dev/active/continuous_swarm.md",
            ),
            context={
                "flow": "start_swarm",
                "step": "preflight",
                "preset_id": "continuous_swarm",
                "plan_doc": "dev/active/continuous_swarm.md",
                "mp_scope": "MP-358",
            },
            busy_label="Swarm...",
            busy_buttons=window._review_action_buttons(),
        )
        self.assertEqual(window.home_workspace.start_swarm_label.text(), "Swarm Preflight")
        self.assertEqual(window.activity_workspace.swarm_status_label.text(), "Swarm Preflight")
        self.assertIn("Preflight:", window.home_workspace.start_swarm_command_label.text())
        self.assertIn("Preflight:", window.activity_workspace.swarm_command_label.text())

    def test_launch_dry_run_uses_json_backend_command(self) -> None:
        from app.operator_console.workflows import build_launch_command

        window = _make_window()
        window._apply_workflow_preset("continuous_swarm", announce=False)
        with patch.object(window, "_start_command", return_value=True) as mock_start:
            window.launch_dry_run()

        mock_start.assert_called_once_with(
            build_launch_command(
                live=False,
                output_format="json",
                refresh_bridge_heartbeat_if_stale=True,
                scope="dev/active/continuous_swarm.md",
                promotion_plan="dev/active/continuous_swarm.md",
            ),
            context={
                "flow": "review_channel",
                "action": "launch",
                "live": False,
                "preset_id": "continuous_swarm",
                "plan_doc": "dev/active/continuous_swarm.md",
                "mp_scope": "MP-358",
            },
            busy_label="Dry Run...",
            busy_buttons=window._dry_run_action_buttons(),
        )

    def test_launch_live_uses_json_backend_command(self) -> None:
        from app.operator_console.workflows import build_launch_command

        window = _make_window()
        window._live_terminal_supported = True
        window._apply_workflow_preset("continuous_swarm", announce=False)
        with patch.object(window, "_start_command", return_value=True) as mock_start:
            window.launch_live()

        mock_start.assert_called_once_with(
            build_launch_command(
                live=True,
                output_format="json",
                refresh_bridge_heartbeat_if_stale=True,
                scope="dev/active/continuous_swarm.md",
                promotion_plan="dev/active/continuous_swarm.md",
            ),
            context={
                "flow": "review_channel",
                "action": "launch",
                "live": True,
                "preset_id": "continuous_swarm",
                "plan_doc": "dev/active/continuous_swarm.md",
                "mp_scope": "MP-358",
            },
            busy_label="Launch...",
            busy_buttons=(window.launch_live_button,),
        )

    def test_run_selected_plan_loop_preflights_selected_workflow_scope(self) -> None:
        from app.operator_console.workflows import (
            build_orchestrate_status_command,
        )

        window = _make_window()
        window._apply_workflow_preset("continuous_swarm", announce=False)
        with patch.object(window, "_start_command", return_value=True) as mock_start:
            window.run_selected_plan_loop()

        mock_start.assert_called_once_with(
            build_orchestrate_status_command(output_format="json"),
            context={
                "flow": "plan_loop_preflight",
                "preset_id": "continuous_swarm",
                "plan_doc": "dev/active/continuous_swarm.md",
                "mp_scope": "MP-358",
            },
            busy_label="Audit...",
            busy_buttons=window._loop_action_buttons(),
        )
        self.assertEqual(window.home_workspace.workflow_status_label.text(), "Loop Audit Running")
        self.assertEqual(window.activity_workspace.workflow_status_label.text(), "Loop Audit Running")
        self.assertIn("MP-358", window.home_workspace.workflow_detail_label.text())

    def test_run_workflow_audit_uses_repo_owned_audit_command(self) -> None:
        from app.operator_console.workflows import (
            build_orchestrate_status_command,
        )

        window = _make_window()
        with patch.object(window, "_start_command", return_value=True) as mock_start:
            window.run_workflow_audit()

        mock_start.assert_called_once_with(
            build_orchestrate_status_command(output_format="json"),
            context={"flow": "workflow_audit", "preset_id": "operator_console"},
            busy_label="Audit...",
            busy_buttons=window._audit_action_buttons(),
        )
        self.assertEqual(window.home_workspace.workflow_status_label.text(), "Workflow Audit Running")
        self.assertEqual(window.activity_workspace.workflow_status_label.text(), "Workflow Audit Running")

    def test_record_decision_uses_typed_command_path(self) -> None:
        from app.operator_console.workflows import (
            build_operator_decision_command,
        )
        from app.operator_console.state.core.models import ApprovalRequest

        window = _make_window()
        approval = ApprovalRequest(
            packet_id="pkt-21",
            from_agent="codex",
            to_agent="operator",
            summary="Approve guarded push",
            body="Need operator approval before push.",
            policy_hint="operator_approval_required",
            requested_action="git_push",
            status="pending",
            evidence_refs=("bridge.md#L1",),
        )

        with patch.object(window, "_start_command", return_value=True) as mock_start:
            window.record_decision("approve", approval=approval, note="Ship it.")

        mock_start.assert_called_once_with(
            build_operator_decision_command(
                approval=approval,
                decision="approve",
                note="Ship it.",
                output_format="json",
            ),
            context={
                "flow": "operator_decision",
                "decision": "approve",
                "packet_id": "pkt-21",
            },
            busy_label="Approve...",
        )

    def test_describe_command_labels_operator_decisions(self) -> None:
        from app.operator_console.workflows import (
            build_operator_decision_command,
        )
        from app.operator_console.state.core.models import ApprovalRequest

        window = _make_window()
        approval = ApprovalRequest(
            packet_id="pkt-22",
            from_agent="codex",
            to_agent="operator",
            summary="Deny guarded push",
            body="Need operator denial for this push.",
            policy_hint="operator_approval_required",
            requested_action="git_push",
            status="pending",
            evidence_refs=(),
        )

        self.assertEqual(
            window._describe_command(
                build_operator_decision_command(
                    approval=approval,
                    decision="deny",
                    output_format="json",
                )
            ),
            "Deny",
        )

    def test_describe_command_labels_workflow_audit_and_loop(self) -> None:
        from app.operator_console.workflows import (
            build_orchestrate_status_command,
            build_swarm_run_command,
        )

        window = _make_window()

        self.assertEqual(
            window._describe_command(build_orchestrate_status_command(output_format="json")),
            "Workflow Audit",
        )
        self.assertEqual(
            window._describe_command(
                build_swarm_run_command(
                    plan_doc="dev/active/operator_console.md",
                    mp_scope="MP-359",
                    output_format="json",
                )
            ),
            "Plan Loop",
        )

    def test_start_swarm_preflight_success_launches_live_command(self) -> None:
        from app.operator_console.workflows import build_launch_command

        window = _make_window()
        window._apply_workflow_preset("continuous_swarm", announce=False)
        report = json.dumps(
            {
                "ok": True,
                "bridge_active": True,
                "codex_lane_count": 2,
                "claude_lane_count": 2,
            }
        )

        with patch.object(window, "_start_command", return_value=True) as mock_start:
            continued = window._handle_start_swarm_completion(
                step="preflight",
                exit_code=0,
                stdout=report,
                stderr="",
            )

        self.assertTrue(continued)
        mock_start.assert_called_once_with(
            build_launch_command(
                live=True,
                output_format="json",
                refresh_bridge_heartbeat_if_stale=True,
                scope="dev/active/continuous_swarm.md",
                promotion_plan="dev/active/continuous_swarm.md",
            ),
            context={
                "flow": "start_swarm",
                "step": "live",
                "preset_id": "continuous_swarm",
                "plan_doc": "dev/active/continuous_swarm.md",
                "mp_scope": "MP-358",
            },
            busy_label="Swarm...",
            busy_buttons=window._review_action_buttons(),
        )
        self.assertEqual(window.home_workspace.start_swarm_label.text(), "Swarm Launching")
        self.assertEqual(window.activity_workspace.swarm_status_label.text(), "Swarm Launching")

    def test_plan_loop_preflight_success_launches_swarm_run_command(self) -> None:
        from app.operator_console.workflows import build_swarm_run_command

        window = _make_window()
        report = json.dumps(
            {
                "ok": True,
                "git": {"branch": "feature/test", "changed_count": 7},
                "warnings": [],
            }
        )

        with patch.object(window, "_start_command", return_value=True) as mock_start:
            continued, message = window._handle_plan_loop_preflight_completion(
                exit_code=0,
                stdout=report,
                stderr="",
                preset_id="continuous_swarm",
                plan_doc="dev/active/continuous_swarm.md",
                mp_scope="MP-358",
            )

        self.assertTrue(continued)
        self.assertEqual(
            message,
            "Workflow audit ok for MP-358. Launching the continuous plan loop.",
        )
        mock_start.assert_called_once_with(
            build_swarm_run_command(
                plan_doc="dev/active/continuous_swarm.md",
                mp_scope="MP-358",
                output_format="json",
                continuous=True,
                continuous_max_cycles=10,
                feedback_sizing=True,
            ),
            context={
                "flow": "plan_loop",
                "preset_id": "continuous_swarm",
                "plan_doc": "dev/active/continuous_swarm.md",
                "mp_scope": "MP-358",
            },
            busy_label="Loop...",
            busy_buttons=window._loop_action_buttons(),
        )
        self.assertEqual(window.home_workspace.workflow_status_label.text(), "Loop Launching")
        self.assertEqual(window.activity_workspace.workflow_status_label.text(), "Loop Launching")

    def test_plan_loop_preflight_failure_blocks_swarm_run(self) -> None:
        window = _make_window()
        report = json.dumps(
            {
                "ok": False,
                "errors": ["active-plan-sync: MASTER_PLAN is out of sync"],
            }
        )

        with patch.object(window, "_start_command", return_value=True) as mock_start:
            continued, message = window._handle_plan_loop_preflight_completion(
                exit_code=1,
                stdout=report,
                stderr="",
                preset_id="operator_console",
                plan_doc="dev/active/operator_console.md",
                mp_scope="MP-359",
            )

        self.assertFalse(continued)
        self.assertEqual(
            message,
            "Plan loop blocked: active-plan-sync: MASTER_PLAN is out of sync",
        )
        mock_start.assert_not_called()
        self.assertEqual(window.home_workspace.workflow_status_label.text(), "Loop Blocked")
        self.assertEqual(window.activity_workspace.workflow_status_label.text(), "Loop Blocked")

    def test_workflow_audit_completion_updates_visible_status(self) -> None:
        window = _make_window()
        window._active_command_context = {
            "flow": "workflow_audit",
            "preset_id": "operator_console",
        }
        window._active_command_stdout = json.dumps(
            {
                "ok": True,
                "git": {"branch": "feature/test", "changed_count": 4},
                "warnings": [],
            }
        )
        window._active_command_stderr = ""

        window._on_process_finished(0, None)

        self.assertEqual(window.home_workspace.workflow_status_label.text(), "Workflow Audit Green")
        self.assertEqual(window.activity_workspace.workflow_status_label.text(), "Workflow Audit Green")
        self.assertIn("feature/test", window.home_workspace.workflow_detail_label.text())

    def test_plan_loop_completion_updates_visible_status(self) -> None:
        window = _make_window()
        window._active_command_context = {
            "flow": "plan_loop",
            "preset_id": "continuous_swarm",
            "plan_doc": "dev/active/continuous_swarm.md",
            "mp_scope": "MP-358",
        }
        window._active_command_stdout = json.dumps(
            {
                "ok": True,
                "mp_scope": "MP-358",
                "run_dir": "/tmp/swarm-run",
                "next_steps": ["Keep the reviewer loop moving."],
                "continuous": {
                    "enabled": True,
                    "max_cycles": 10,
                    "cycles_completed": 10,
                    "stop_reason": "max_cycles_reached",
                },
            }
        )
        window._active_command_stderr = ""

        window._on_process_finished(0, None)

        self.assertEqual(window.home_workspace.workflow_status_label.text(), "Loop Complete")
        self.assertEqual(window.activity_workspace.workflow_status_label.text(), "Loop Complete")
        self.assertIn("MP-358", window.home_workspace.workflow_detail_label.text())

    def test_start_swarm_preflight_failure_blocks_live_command(self) -> None:
        window = _make_window()
        window._apply_workflow_preset("continuous_swarm", announce=False)
        report = json.dumps(
            {
                "ok": True,
                "bridge_active": False,
                "codex_lane_count": 2,
                "claude_lane_count": 2,
            }
        )

        with patch.object(window, "_start_command", return_value=True) as mock_start:
            continued = window._handle_start_swarm_completion(
                step="preflight",
                exit_code=0,
                stdout=report,
                stderr="",
            )

        self.assertFalse(continued)
        mock_start.assert_not_called()
        self.assertEqual(window.home_workspace.start_swarm_label.text(), "Swarm Blocked")
        self.assertEqual(window.activity_workspace.swarm_status_label.text(), "Swarm Blocked")
        self.assertEqual(
            window.home_workspace.start_swarm_dot.property("statusLevel"),
            "stale",
        )
        self.assertEqual(
            window.activity_workspace.swarm_status_dot.property("statusLevel"),
            "stale",
        )

    def test_start_swarm_live_success_updates_visible_status(self) -> None:
        window = _make_window()
        window._apply_workflow_preset("continuous_swarm", announce=False)
        report = json.dumps(
            {
                "ok": True,
                "launched": True,
                "codex_lane_count": 2,
                "claude_lane_count": 2,
            }
        )

        continued = window._handle_start_swarm_completion(
            step="live",
            exit_code=0,
            stdout=report,
            stderr="",
        )

        self.assertFalse(continued)
        self.assertEqual(window.home_workspace.start_swarm_label.text(), "Swarm Running")
        self.assertEqual(window.activity_workspace.swarm_status_label.text(), "Swarm Running")
        self.assertEqual(
            window.home_workspace.start_swarm_dot.property("statusLevel"),
            "active",
        )
        self.assertEqual(
            window.activity_workspace.swarm_status_dot.property("statusLevel"),
            "active",
        )

    def test_live_controls_disable_when_terminal_app_is_unavailable(self) -> None:
        with patch(
            "app.operator_console.views.main_window.terminal_app_live_supported",
            return_value=False,
        ), patch(
            "app.operator_console.views.main_window.terminal_app_live_support_detail",
            return_value="Terminal.app live controls require macOS. Use Launch Dry Run instead.",
        ):
            window = _make_window()

        self.assertFalse(window.launch_live_button.isEnabled())
        self.assertFalse(window.rollover_button.isEnabled())
        self.assertFalse(window.home_workspace.start_swarm_button.isEnabled())
        self.assertFalse(window.activity_workspace.activity_start_swarm_button.isEnabled())
        self.assertTrue(window.launch_dry_button.isEnabled())
        self.assertEqual(window.home_workspace.start_swarm_label.text(), "Swarm Live-Gated")
        self.assertIn("Terminal.app", window.launch_live_button.toolTip())

    def test_start_swarm_refuses_when_terminal_app_is_unavailable(self) -> None:
        with patch(
            "app.operator_console.views.main_window.terminal_app_live_supported",
            return_value=False,
        ), patch(
            "app.operator_console.views.main_window.terminal_app_live_support_detail",
            return_value="Terminal.app live controls require macOS. Use Launch Dry Run instead.",
        ):
            window = _make_window()

        with patch.object(window, "_start_command") as mock_start:
            window.start_swarm()

        mock_start.assert_not_called()
        self.assertEqual(window.home_workspace.start_swarm_label.text(), "Swarm Live-Gated")
        self.assertIn("Launch Dry Run", window.command_output.toPlainText())

    def test_live_launch_failure_surfaces_backend_error(self) -> None:
        window = _make_window()
        message = (
            "Fresh conductor bootstrap requires a green review-channel bridge "
            "guard before launch."
        )
        window._process = MagicMock()
        window._active_command_context = {
            "flow": "review_channel",
            "action": "launch",
            "live": True,
        }
        window._active_command_label = "Launch"
        window._active_command_stdout = json.dumps(
            {
                "ok": False,
                "errors": [message],
            }
        )
        window._active_command_stderr = ""

        with patch.object(window, "refresh_snapshot") as mock_refresh:
            window._on_process_finished(1, object())

        mock_refresh.assert_called_once()
        self.assertIn(message, window.command_output.toPlainText())
        self.assertEqual(window.statusBar().currentMessage(), message)
        self.assertTrue(
            any(
                call.kwargs.get("event") == "review_channel_command_failed"
                for call in window.diagnostics.log.call_args_list
            )
        )

    def test_failed_to_start_command_surfaces_immediately(self) -> None:
        window = _make_window()
        process = MagicMock()
        process.errorString.return_value = "execve failed"
        window._process = process
        window._active_command_label = "Launch"
        window._active_command_context = {
            "flow": "review_channel",
            "action": "launch",
            "live": True,
        }
        window._set_command_controls_busy(True, label="Launch...")

        window._on_process_error(process, QProcess.ProcessError.FailedToStart)

        self.assertIn("Launch could not start: execve failed", window.command_output.toPlainText())
        self.assertEqual(
            window.statusBar().currentMessage(),
            "Launch could not start: execve failed",
        )
        self.assertTrue(window.launch_live_button.isEnabled())
        self.assertIsNone(window._process)
        self.assertTrue(
            any(
                call.kwargs.get("event") == "command_failed_to_start"
                for call in window.diagnostics.log.call_args_list
            )
        )

    def test_analytics_panel_uses_honest_repo_signal_copy(self) -> None:
        window = _make_window()

        analytics_text = window._analytics_text.toPlainText()

        self.assertIn("REPO-VISIBLE REVIEW SIGNALS", analytics_text)
        self.assertIn("phone-status artifacts", analytics_text)

    def test_operator_decision_completion_clears_note_and_logs_typed_result(self) -> None:
        window = _make_window()
        window.approval_panel._note_input.setText("Looks good.")
        window._process = MagicMock()
        window._active_command_context = {
            "flow": "operator_decision",
            "decision": "approve",
            "packet_id": "pkt-23",
        }
        window._active_command_stdout = json.dumps(
            {
                "ok": True,
                "message": (
                    "Recorded operator approve artifact for pkt-23 through the typed "
                    "wrapper command. Direct devctl review-channel ack|apply|dismiss "
                    "is not available yet."
                ),
                "decision": "approve",
                "packet_id": "pkt-23",
                "typed_action_mode": "wrapper_artifact_command",
                "devctl_review_channel_action_available": False,
                "artifact": {
                    "json_path": "/tmp/pkt-23.json",
                    "markdown_path": "/tmp/pkt-23.md",
                    "latest_json_path": "/tmp/latest.json",
                    "latest_markdown_path": "/tmp/latest.md",
                },
            }
        )
        window._active_command_stderr = ""

        with patch.object(window, "refresh_snapshot") as mock_refresh:
            window._on_process_finished(0, object())

        mock_refresh.assert_called_once()
        self.assertEqual(window.approval_panel.note_text, "")
        self.assertIn("typed wrapper command", window.command_output.toPlainText())
        self.assertEqual(
            window.statusBar().currentMessage(),
            (
                "Recorded operator approve artifact for pkt-23 through the typed "
                "wrapper command. Direct devctl review-channel ack|apply|dismiss "
                "is not available yet."
            ),
        )
        self.assertTrue(
            any(
                call.kwargs.get("event") == "operator_decision_recorded"
                for call in window.diagnostics.log.call_args_list
            )
        )

    def test_menu_bar_exposes_help_and_developer_menus(self) -> None:
        window = _make_window()
        labels = [action.text() for action in window.menuBar().actions()]
        self.assertIn("&Run", labels)
        self.assertIn("&View", labels)
        self.assertIn("&Theme", labels)
        self.assertIn("&Settings", labels)
        self.assertIn("&Help", labels)
        self.assertIn("&Developer", labels)

    def test_toolbar_settings_have_tooltips(self) -> None:
        window = _make_window()
        self.assertIn("simple and technical", window.read_mode_combo.toolTip().lower())
        self.assertIn("desktop theme", window.theme_combo.toolTip().lower())
        self.assertIn("arranged", window.layout_combo.toolTip().lower())
        self.assertIn("acknowledgements", window.ack_wait_spin.toolTip().lower())


if __name__ == "__main__":
    unittest.main()
