"""Tests for layout mode registry, layout switching, and layout-specific
widget structure (sidebar nav, grid cells, analytics KPIs)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from .test_ui_layout import _blank_snapshot
from app.operator_console.views.layout.ui_layouts import (
    DEFAULT_LAYOUT_ID,
    DEFAULT_WORKBENCH_PRESET_ID,
    LAYOUT_REGISTRY,
    WORKBENCH_PRESET_REGISTRY,
    available_layout_ids,
    available_workbench_preset_ids,
    resolve_layout,
    resolve_workbench_preset,
)

try:
    from PyQt6.QtWidgets import QApplication

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QApplication = None


def _make_window(
    *,
    layout_mode: str = DEFAULT_LAYOUT_ID,
    theme_id: str = "codex",
    repo: Path | None = None,
    persist_layout_state: bool = False,
):
    """Build an OperatorConsoleWindow with mocked bridge data."""
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
        engine = ThemeEngine()
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


# ── Registry tests ───────────────────────────────────────────


class LayoutRegistryTests(unittest.TestCase):
    def test_default_layout_id_is_workbench(self) -> None:
        self.assertEqual(DEFAULT_LAYOUT_ID, "workbench")

    def test_available_layout_ids_returns_all_modes(self) -> None:
        ids = available_layout_ids()
        self.assertEqual(ids, ("tabbed", "sidebar", "grid", "analytics", "workbench"))

    def test_available_workbench_preset_ids_returns_all_presets(self) -> None:
        self.assertEqual(
            available_workbench_preset_ids(),
            ("balanced", "lanes", "launch", "activity"),
        )

    def test_resolve_unknown_falls_back_to_default(self) -> None:
        desc = resolve_layout("nonexistent")
        self.assertEqual(desc.mode_id, DEFAULT_LAYOUT_ID)

    def test_resolve_known_returns_correct_descriptor(self) -> None:
        desc = resolve_layout("sidebar")
        self.assertEqual(desc.mode_id, "sidebar")
        self.assertEqual(desc.display_name, "Sidebar")

    def test_every_registry_entry_has_nonempty_fields(self) -> None:
        for desc in LAYOUT_REGISTRY:
            self.assertTrue(desc.mode_id)
            self.assertTrue(desc.display_name)
            self.assertTrue(desc.description)

    def test_default_workbench_preset_is_balanced(self) -> None:
        self.assertEqual(DEFAULT_WORKBENCH_PRESET_ID, "balanced")

    def test_every_workbench_preset_entry_has_nonempty_fields(self) -> None:
        for desc in WORKBENCH_PRESET_REGISTRY:
            self.assertTrue(desc.preset_id)
            self.assertTrue(desc.display_name)
            self.assertTrue(desc.description)
            self.assertEqual(len(desc.root_sizes), 2)
            self.assertEqual(len(desc.lane_sizes), 3)
            self.assertEqual(len(desc.utility_sizes), 3)

    def test_resolve_unknown_workbench_preset_falls_back_to_default(self) -> None:
        desc = resolve_workbench_preset("unknown")
        self.assertEqual(desc.preset_id, DEFAULT_WORKBENCH_PRESET_ID)


# ── Tabbed layout tests ─────────────────────────────────────


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class TabbedLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_tabbed_creates_nav_tabs(self) -> None:
        window = _make_window(layout_mode="tabbed")
        self.assertEqual(window._nav_tabs.count(), 5)

    def test_tabbed_tab_labels(self) -> None:
        window = _make_window(layout_mode="tabbed")
        labels = [
            window._nav_tabs.tabText(i)
            for i in range(window._nav_tabs.count())
        ]
        self.assertEqual(labels, ["Home", "Dashboard", "Monitor", "Activity", "Collaborate"])

    def test_tabbed_lane_dots_exist(self) -> None:
        window = _make_window(layout_mode="tabbed")
        self.assertIsNotNone(window._codex_lane_dot)
        self.assertIsNotNone(window._claude_lane_dot)
        self.assertIsNotNone(window._cursor_lane_dot)
        self.assertIsNotNone(window._operator_lane_dot)


# ── Sidebar layout tests ────────────────────────────────────


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class SidebarLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_sidebar_creates_nav_list(self) -> None:
        window = _make_window(layout_mode="sidebar")
        self.assertIsNotNone(getattr(window, "_sidebar_nav", None))

    def test_sidebar_nav_has_fourteen_items(self) -> None:
        window = _make_window(layout_mode="sidebar")
        self.assertEqual(window._sidebar_nav.count(), 14)

    def test_sidebar_nav_first_item_is_home(self) -> None:
        from PyQt6.QtCore import Qt

        window = _make_window(layout_mode="sidebar")
        item = window._sidebar_nav.item(0)
        self.assertEqual(item.text(), "Home")
        self.assertEqual(item.data(Qt.ItemDataRole.UserRole), "home")

    def test_sidebar_nav_items_have_tooltips(self) -> None:
        window = _make_window(layout_mode="sidebar")
        item = window._sidebar_nav.item(0)
        self.assertIn("guided start screen", item.toolTip().lower())

    def test_sidebar_stack_matches_nav_count(self) -> None:
        window = _make_window(layout_mode="sidebar")
        self.assertEqual(
            window._sidebar_stack.count(), window._sidebar_nav.count()
        )

    def test_sidebar_starts_on_first_page(self) -> None:
        window = _make_window(layout_mode="sidebar")
        self.assertEqual(window._sidebar_stack.currentIndex(), 0)


# ── Grid layout tests ───────────────────────────────────────


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class GridLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_grid_layout_mode_is_set(self) -> None:
        window = _make_window(layout_mode="grid")
        self.assertEqual(window._layout_mode, "grid")

    def test_grid_shows_all_panels(self) -> None:
        """In grid mode, all KV panels should be parented (not orphaned)."""
        window = _make_window(layout_mode="grid")
        self.assertIsNotNone(window.codex_panel.parent())
        self.assertIsNotNone(window.cursor_panel.parent())
        self.assertIsNotNone(window.claude_panel.parent())
        self.assertIsNotNone(window.operator_panel.parent())

    def test_grid_command_output_is_parented(self) -> None:
        window = _make_window(layout_mode="grid")
        self.assertIsNotNone(window.command_output.parent())

    def test_grid_approval_panel_is_parented(self) -> None:
        window = _make_window(layout_mode="grid")
        self.assertIsNotNone(window._approval_container.parent())


# ── Analytics layout tests ───────────────────────────────────


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class AnalyticsLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_analytics_creates_kpi_cards(self) -> None:
        window = _make_window(layout_mode="analytics")
        self.assertIsNotNone(getattr(window, "_kpi_cards", None))
        self.assertGreater(len(window._kpi_cards), 0)

    def test_analytics_kpi_card_ids(self) -> None:
        window = _make_window(layout_mode="analytics")
        expected = {
            "dirty_files",
            "mutation_score",
            "ci_runs",
            "warnings",
            "pending_approvals",
            "phone_phase",
        }
        self.assertEqual(set(window._kpi_cards.keys()), expected)

    def test_analytics_text_is_parented(self) -> None:
        window = _make_window(layout_mode="analytics")
        self.assertIsNotNone(window._analytics_text.parent())

    def test_analytics_repo_text_is_parented(self) -> None:
        window = _make_window(layout_mode="analytics")
        self.assertIsNotNone(window._analytics_repo_text.parent())

    def test_analytics_phone_text_is_parented(self) -> None:
        window = _make_window(layout_mode="analytics")
        self.assertIsNotNone(window._analytics_phone_text.parent())

    def test_analytics_approval_panel_is_parented(self) -> None:
        window = _make_window(layout_mode="analytics")
        self.assertIsNotNone(window._approval_container.parent())


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class WorkbenchLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_workbench_layout_mode_is_set(self) -> None:
        window = _make_window(layout_mode="workbench")
        self.assertEqual(window._layout_mode, "workbench")

    def test_workbench_creates_nested_splitters(self) -> None:
        window = _make_window(layout_mode="workbench")
        self.assertIsNotNone(getattr(window, "_workbench_lane_splitter", None))
        self.assertIsNotNone(getattr(window, "_workbench_utility_splitter", None))
        self.assertIsNone(getattr(window, "_workbench_root_splitter", None))

    def test_workbench_exposes_preset_buttons(self) -> None:
        window = _make_window(layout_mode="workbench")
        self.assertEqual(window._workbench_preset_buttons, {})
        self.assertEqual(window._workbench_preset, DEFAULT_WORKBENCH_PRESET_ID)

    def test_workbench_groups_lower_deck_into_function_tabs(self) -> None:
        window = _make_window(layout_mode="workbench")
        labels = [
            window._workbench_tabs.tabText(i)
            for i in range(window._workbench_tabs.count())
        ]
        self.assertEqual(
            labels,
            ["Sessions", "Terminal", "Stats", "Approvals", "Reports"],
        )

    def test_workbench_keeps_terminal_cards_parented(self) -> None:
        window = _make_window(layout_mode="workbench")
        self.assertIsNotNone(window._monitor_tabs)
        self.assertEqual(
            window._monitor_tabs.currentIndex(),
            window._monitor_surface_indexes["command_output"],
        )
        self.assertIsNotNone(window.codex_session_text.parent())
        self.assertIsNotNone(window.codex_session_detail_card)
        self.assertIsNotNone(window.codex_session_stats_text.parent())
        self.assertIsNotNone(window.codex_session_registry_text.parent())
        self.assertIsNotNone(window.claude_session_text.parent())
        self.assertIsNotNone(window.claude_session_detail_card)
        self.assertIsNotNone(window.claude_session_stats_text.parent())
        self.assertIsNotNone(window.claude_session_registry_text.parent())
        self.assertIsNotNone(window.cursor_session_text.parent())
        self.assertIsNotNone(window.cursor_session_detail_card)
        self.assertIsNotNone(window.cursor_session_stats_text.parent())
        self.assertIsNotNone(window.cursor_session_registry_text.parent())
        self.assertIsNotNone(window.command_output.parent())
        self.assertIsNotNone(window.raw_bridge_text.parent())
        self.assertIsNotNone(window.timeline_panel.parent())
        self.assertIsNotNone(window.dev_log_text.parent())
        self.assertIsNotNone(window._workbench_tabs.parent())
        self.assertIsNotNone(window.workflow_header_bar.parent())
        self.assertIsNotNone(window.workflow_timeline_footer.parent())

    def test_workbench_terminal_surface_exposes_timeline_tab(self) -> None:
        window = _make_window(layout_mode="workbench")
        labels = [
            window._monitor_tabs.tabText(i)
            for i in range(window._monitor_tabs.count())
        ]
        self.assertEqual(labels, ["Timeline", "Bridge", "Launcher Output", "Diagnostics"])
        self.assertIn("timeline", window._monitor_surface_indexes)

    def test_workbench_footer_exposes_transition_stages(self) -> None:
        window = _make_window(layout_mode="workbench")
        stage_labels = window.workflow_timeline_footer._stage_labels
        self.assertEqual(
            tuple(stage_labels.keys()),
            (
                "posted",
                "read",
                "acked",
                "implementing",
                "tests",
                "reviewed",
                "apply",
            ),
        )

    def test_workbench_starts_on_sessions_page(self) -> None:
        window = _make_window(layout_mode="workbench")
        self.assertEqual(
            window._workbench_tabs.currentIndex(),
            window._workbench_surface_indexes["sessions"],
        )

    def test_workbench_home_buttons_route_to_function_tabs(self) -> None:
        window = _make_window(layout_mode="workbench")
        window._open_activity_surface()
        self.assertEqual(
            window._workbench_tabs.currentIndex(),
            window._workbench_surface_indexes["reports"],
        )
        window._open_monitor_surface()
        self.assertEqual(
            window._workbench_tabs.currentIndex(),
            window._workbench_surface_indexes["terminal"],
        )
        window._navigate_primary_surface("home")
        self.assertEqual(
            window._workbench_tabs.currentIndex(),
            window._workbench_surface_indexes["sessions"],
        )

    def test_workbench_reveal_output_returns_to_terminal_tab(self) -> None:
        window = _make_window(layout_mode="workbench")
        window._open_activity_surface()
        window._reveal_output_surface("diagnostics")
        self.assertEqual(
            window._workbench_tabs.currentIndex(),
            window._workbench_surface_indexes["terminal"],
        )
        self.assertEqual(
            window._monitor_tabs.currentIndex(),
            window._monitor_surface_indexes["diagnostics"],
        )


# ── Layout switching tests ───────────────────────────────────


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class LayoutSwitchingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_switch_from_tabbed_to_sidebar(self) -> None:
        window = _make_window(layout_mode="tabbed")
        self.assertEqual(window._layout_mode, "tabbed")
        with patch(
            "app.operator_console.views.ui_refresh.build_operator_console_snapshot"
        ) as mock_snap:
            mock_snap.return_value = _blank_snapshot()
            window._switch_layout("sidebar")
        self.assertEqual(window._layout_mode, "sidebar")

    def test_switch_preserves_panel_text(self) -> None:
        """Data widget content should survive layout switches."""
        window = _make_window(layout_mode="tabbed")
        window.raw_bridge_text.setPlainText("test content")
        with patch(
            "app.operator_console.views.ui_refresh.build_operator_console_snapshot"
        ) as mock_snap:
            mock_snap.return_value = _blank_snapshot()
            window._switch_layout("grid")
        self.assertEqual(window.raw_bridge_text.toPlainText(), "test content")

    def test_switch_to_analytics_and_back(self) -> None:
        window = _make_window(layout_mode="tabbed")
        with patch(
            "app.operator_console.views.ui_refresh.build_operator_console_snapshot"
        ) as mock_snap:
            mock_snap.return_value = _blank_snapshot()
            window._switch_layout("analytics")
            self.assertEqual(window._layout_mode, "analytics")
            window._switch_layout("tabbed")
            self.assertEqual(window._layout_mode, "tabbed")

    def test_switching_away_from_analytics_clears_kpi_refs(self) -> None:
        window = _make_window(layout_mode="analytics")
        self.assertTrue(window._kpi_cards)
        window._switch_layout("grid")
        self.assertEqual(window._kpi_cards, {})

    def test_refresh_after_analytics_switch_survives_deferred_delete(self) -> None:
        from PyQt6.QtCore import QCoreApplication, QEvent

        window = _make_window(layout_mode="analytics")
        with patch(
            "app.operator_console.views.ui_refresh.build_operator_console_snapshot"
        ) as mock_snap:
            mock_snap.return_value = _blank_snapshot()
            window._switch_layout("grid")
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.app.processEvents()
            window.refresh_snapshot()

        refresh_failures = [
            call
            for call in window.diagnostics.log.call_args_list
            if call.kwargs.get("event") == "refresh_failed"
        ]
        self.assertEqual(refresh_failures, [])

    def test_refresh_snapshot_logs_exceptions_instead_of_raising(self) -> None:
        window = _make_window(layout_mode="tabbed")
        with patch(
            "app.operator_console.views.ui_refresh.build_operator_console_snapshot",
            side_effect=RuntimeError("boom"),
        ):
            window.refresh_snapshot()

        refresh_failure_calls = [
            call
            for call in window.diagnostics.log.call_args_list
            if call.kwargs.get("event") == "refresh_failed"
        ]
        self.assertEqual(len(refresh_failure_calls), 1)
        self.assertIn("RuntimeError: boom", window.statusBar().currentMessage())

    def test_layout_combo_has_all_modes(self) -> None:
        window = _make_window()
        items = [
            window.layout_combo.itemData(i)
            for i in range(window.layout_combo.count())
        ]
        self.assertEqual(
            items, ["tabbed", "sidebar", "grid", "analytics", "workbench"]
        )

    def test_workbench_layout_state_round_trips_last_selected_tabs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            window = _make_window(
                layout_mode="workbench",
                repo=repo,
                persist_layout_state=True,
            )
            window._select_workbench_surface("terminal")
            window._select_monitor_surface("diagnostics")
            window._persist_layout_state()

            restored = _make_window(
                layout_mode="tabbed",
                repo=repo,
                persist_layout_state=True,
            )

        self.assertEqual(restored._layout_mode, "workbench")
        self.assertEqual(
            restored._workbench_tabs.currentIndex(),
            restored._workbench_surface_indexes["terminal"],
        )
        self.assertEqual(
            restored._monitor_tabs.currentIndex(),
            restored._monitor_surface_indexes["diagnostics"],
        )

    def test_layout_state_export_writes_snapshot_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            window = _make_window(
                layout_mode="workbench",
                repo=repo,
                persist_layout_state=True,
            )
            window._select_workbench_surface("terminal")
            window._select_monitor_surface("timeline")
            window._export_layout_state_snapshot()
            export_path = window._layout_state_export_path()
            self.assertIsNotNone(export_path)
            assert export_path is not None
            self.assertTrue(export_path.exists())

    def test_layout_state_import_restores_exported_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            window = _make_window(
                layout_mode="workbench",
                repo=repo,
                persist_layout_state=True,
            )
            window._select_workbench_surface("terminal")
            window._select_monitor_surface("diagnostics")
            window._export_layout_state_snapshot()

            window._select_workbench_surface("sessions")
            window._select_monitor_surface("bridge")
            window._import_layout_state_snapshot()

        self.assertEqual(
            window._workbench_tabs.currentIndex(),
            window._workbench_surface_indexes["terminal"],
        )
        self.assertEqual(
            window._monitor_tabs.currentIndex(),
            window._monitor_surface_indexes["diagnostics"],
        )

    def test_layout_state_reset_restores_default_workbench_targets(self) -> None:
        window = _make_window(layout_mode="workbench", persist_layout_state=False)
        window._select_workbench_surface("terminal")
        window._select_monitor_surface("bridge")

        window._reset_layout_state()

        self.assertEqual(
            window._workbench_tabs.currentIndex(),
            window._workbench_surface_indexes["sessions"],
        )
        self.assertEqual(
            window._monitor_tabs.currentIndex(),
            window._monitor_surface_indexes["command_output"],
        )


# ── Theme stylesheet tests for new selectors ─────────────────


class SidebarStylesheetTests(unittest.TestCase):
    def test_sidebar_nav_has_qss_rule(self) -> None:
        from app.operator_console.theme import build_operator_console_stylesheet

        stylesheet = build_operator_console_stylesheet("codex")
        self.assertIn("QFrame#SidebarNav", stylesheet)
        self.assertIn("QListWidget#SidebarNavList", stylesheet)

    def test_kpi_card_has_qss_rule(self) -> None:
        from app.operator_console.theme import build_operator_console_stylesheet

        stylesheet = build_operator_console_stylesheet("codex")
        self.assertIn("QFrame#KPICard", stylesheet)
        self.assertIn("QLabel#KPIValue", stylesheet)
        self.assertIn("QLabel#KPILabel", stylesheet)


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class ThemeSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_window_bootstraps_engine_from_requested_theme_id(self) -> None:
        window = _make_window(theme_id="claude")

        self.assertEqual(window._theme_engine.current_theme_id, "claude")
        self.assertEqual(window.theme_combo.currentData(), "claude")

    def test_theme_combo_tracks_draft_state_after_theme_edit(self) -> None:
        window = _make_window(theme_id="codex")

        window._theme_engine.set_color("accent", "#123456")

        self.assertIsNone(window._theme_engine.current_theme_id)
        self.assertEqual(
            window.theme_combo.currentData(),
            window._dynamic_theme_combo_data,
        )
        self.assertIn("Draft:", window.theme_combo.currentText())


if __name__ == "__main__":
    unittest.main()
