"""PyQt6 UI for the optional review-channel Operator Console.

This module is the slim orchestrator — it wires together widget creation,
page layout (ui_pages), data refresh (ui_refresh), and scroll helpers
(ui_scroll) without containing any of that logic itself.
"""

from __future__ import annotations

from pathlib import Path

from ..launch_support import (
    manual_module_launch_command,
    manual_pyqt6_install_command,
    preferred_launcher_command,
)
from ..workflows import terminal_app_live_support_detail, terminal_app_live_supported
from ..layout.layout_state import (
    LayoutStateSnapshot,
    default_layout_state_path,
    load_layout_state,
)
from ..workflows.workflow_presets import DEFAULT_WORKFLOW_PRESET_ID
from ..logging_support import OperatorConsoleDiagnostics
from ..theme import (
    available_theme_ids,
    get_engine,
    resolve_theme,
)
from .workspaces.home_workspace import HomeWorkspace
from .workspaces.activity_workspace import ActivityWorkspace
from .approval_panel import ApprovalQueuePanel
from .collaboration.conversation_panel import ConversationPanel
from .collaboration.task_board_panel import TaskBoardPanel
from .collaboration.timeline_panel import TimelinePanel
from .workflow.workflow_surface import WorkflowHeaderBar, WorkflowTimelineFooter
from .layout.ui_layouts import (
    DEFAULT_LAYOUT_ID,
    DEFAULT_WORKBENCH_PRESET_ID,
    available_layout_ids,
    resolve_layout,
    resolve_workbench_preset,
)
from .actions.ui_activity_actions import ActivityActionsMixin
from .collaboration.ui_collaboration import CollaborationMixin
from .layout.ui_layout_state import LayoutStateMixin
from .actions.ui_operator_actions import OperatorDecisionMixin
from .ui_pages import PageBuilderMixin
from .actions.ui_commands import CommandActionsMixin
from .actions.ui_process_results import ProcessResultsMixin
from .ui_refresh import RefreshMixin
from .actions.ui_review_actions import ReviewLaunchActionsMixin
from .actions.ui_swarm_status import SwarmStatusMixin
from .layout.ui_window_shell import HAS_THEME_EDITOR, WindowShellMixin
from .workflow.ui_workflow import WorkflowControlsMixin
from .shared.ui_scroll import append_plain_text_preserving_scroll
from .shared.widgets import AgentSummaryCard, KeyValuePanel, StatusIndicator

try:
    from PyQt6.QtCore import QProcess, QTimer, Qt
    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QDialog,
        QMainWindow,
        QPlainTextEdit,
        QPushButton,
        QSpinBox,
        QStatusBar,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - optional dependency path
    QApplication = None
    QMainWindow = object
    IMPORT_ERROR = exc
else:  # pragma: no cover - exercised manually when PyQt6 is installed
    IMPORT_ERROR = None


class OperatorConsoleWindow(
    PageBuilderMixin,
    WindowShellMixin,
    LayoutStateMixin,
    WorkflowControlsMixin,
    SwarmStatusMixin,
    ReviewLaunchActionsMixin,
    ActivityActionsMixin,
    OperatorDecisionMixin,
    ProcessResultsMixin,
    CommandActionsMixin,
    CollaborationMixin,
    RefreshMixin,
    QMainWindow,
):  # pragma: no cover - manual UI path
    """Main window for the optional desktop Operator Console.

    Layout and refresh logic live in PageBuilderMixin and RefreshMixin
    to keep this file focused on widget creation and wiring.
    """

    def __init__(
        self,
        repo_root: Path,
        *,
        diagnostics: OperatorConsoleDiagnostics,
        dev_log_enabled: bool,
        theme_id: str | None,
        layout_mode: str = DEFAULT_LAYOUT_ID,
        persist_layout_state: bool = True,
        layout_state_path: Path | None = None,
    ) -> None:
        super().__init__()
        self._initialize_window_state(
            repo_root=repo_root,
            diagnostics=diagnostics,
            dev_log_enabled=dev_log_enabled,
            layout_mode=layout_mode,
        )
        self._restore_saved_layout_state(
            persist_layout_state=persist_layout_state,
            layout_state_path=layout_state_path,
        )
        self._create_persistent_data_widgets()
        self._create_toolbar_controls()
        self._wire_ui_signals()
        self._finalize_theme_and_modes(theme_id)
        self._build_window_shell()
        self._start_polling_timer()

        self._record_event(
            "INFO",
            "ui_ready",
            "Operator Console window initialized",
            details={
                "dev_log_enabled": self.dev_log_enabled,
                "diagnostics_destination": self.diagnostics.destination_summary,
                "repo_root": self.repo_root,
                "layout_mode": self._layout_mode,
            },
        )
        self.refresh_snapshot()

    def _initialize_window_state(
        self,
        *,
        repo_root: Path,
        diagnostics: OperatorConsoleDiagnostics,
        dev_log_enabled: bool,
        layout_mode: str,
    ) -> None:
        self.repo_root = repo_root
        self.diagnostics = diagnostics
        self.dev_log_enabled = dev_log_enabled
        self.theme_id: str | None = None
        self._layout_mode = resolve_layout(layout_mode).mode_id
        self._workbench_preset = DEFAULT_WORKBENCH_PRESET_ID
        self._layout_state_path: Path | None = None
        self._pending_layout_state: LayoutStateSnapshot | None = None
        self._layout_state_ready = False
        self._process: QProcess | None = None
        self._active_command_label: str | None = None
        self._active_command_context: dict[str, object] | None = None
        self._active_command_stdout = ""
        self._active_command_stderr = ""
        self._last_snapshot_digest: str | None = None
        self._theme_editor_dialog: QDialog | None = None
        self._theme_engine = get_engine()
        self._dynamic_theme_combo_data = "__active_theme__"
        self._help_dialog: QDialog | None = None
        self._audience_mode = "simple"
        self._workflow_preset_id = DEFAULT_WORKFLOW_PRESET_ID
        self._live_terminal_supported = terminal_app_live_supported()
        self._live_terminal_support_detail = terminal_app_live_support_detail()
        self.setWindowTitle("VoiceTerm Operator Console")
        self.resize(1720, 1040)

    def _restore_saved_layout_state(
        self,
        *,
        persist_layout_state: bool,
        layout_state_path: Path | None,
    ) -> None:
        if not persist_layout_state:
            return
        resolved_state_path = (
            layout_state_path
            if layout_state_path is not None
            else default_layout_state_path(self.repo_root)
        )
        self._layout_state_path = resolved_state_path
        loaded_state = load_layout_state(resolved_state_path)
        if loaded_state is None:
            return
        self._pending_layout_state = loaded_state
        self._layout_mode = resolve_layout(loaded_state.layout_mode).mode_id
        self._workbench_preset = resolve_workbench_preset(
            loaded_state.workbench_preset
        ).preset_id

    def _create_persistent_data_widgets(self) -> None:
        self._create_lane_widgets()
        self._create_session_widgets()
        self._create_workspace_widgets()
        self._create_analytics_widgets()
        self._create_collaboration_widgets()

    def _create_lane_widgets(self) -> None:
        self.codex_dot = StatusIndicator()
        self.claude_dot = StatusIndicator()
        self.cursor_dot = StatusIndicator()
        self.operator_dot = StatusIndicator()
        self._codex_lane_dot = StatusIndicator()
        self._claude_lane_dot = StatusIndicator()
        self._cursor_lane_dot = StatusIndicator()
        self._operator_lane_dot = StatusIndicator()
        self.codex_panel = KeyValuePanel("Codex Bridge Monitor")
        self.claude_panel = KeyValuePanel("Claude Bridge Monitor")
        self.cursor_panel = KeyValuePanel("Cursor Bridge Monitor")
        self.operator_panel = KeyValuePanel("Operator Bridge State")

    def _create_session_widgets(self) -> None:
        self.codex_session_text = self._make_readonly_panel(
            "Codex terminal history will appear here.",
            tooltip=(
                "Reviewer terminal history. Prefers live review-channel session "
                "traces when available and falls back to a bridge-derived digest."
            ),
        )
        self.codex_session_stats_text = self._make_readonly_panel(
            "Codex session metadata and live trace signals will appear here.",
            wrap_lines=True,
            tooltip=(
                "Reviewer session metadata, freshness, token/context hints, and "
                "a trimmed current-screen snapshot."
            ),
        )
        self.codex_session_registry_text = self._make_readonly_panel(
            "Codex agent-registry rows will appear here.",
            tooltip="Reviewer lane registry sourced from the review-channel full projection.",
        )
        self.claude_session_text = self._make_readonly_panel(
            "Claude terminal history will appear here.",
            tooltip=(
                "Implementer terminal history. Prefers live review-channel session "
                "traces when available and falls back to a bridge-derived digest."
            ),
        )
        self.claude_session_stats_text = self._make_readonly_panel(
            "Claude session metadata and live trace signals will appear here.",
            wrap_lines=True,
            tooltip=(
                "Implementer session metadata, freshness, token/context hints, and "
                "a trimmed current-screen snapshot."
            ),
        )
        self.claude_session_registry_text = self._make_readonly_panel(
            "Claude agent-registry rows will appear here.",
            tooltip="Implementer lane registry sourced from the review-channel full projection.",
        )
        self.cursor_session_text = self._make_readonly_panel(
            "Cursor terminal history will appear here.",
            tooltip=(
                "Cursor editor terminal history. Prefers live review-channel session "
                "traces when available and falls back to a bridge-derived digest."
            ),
        )
        self.cursor_session_stats_text = self._make_readonly_panel(
            "Cursor session metadata and live trace signals will appear here.",
            wrap_lines=True,
            tooltip=(
                "Cursor editor session metadata, freshness, token/context hints, and "
                "a trimmed current-screen snapshot."
            ),
        )
        self.cursor_session_registry_text = self._make_readonly_panel(
            "Cursor agent-registry rows will appear here.",
            tooltip="Cursor lane registry sourced from the review-channel full projection.",
        )

    def _create_workspace_widgets(self) -> None:
        self.home_workspace = HomeWorkspace()
        self.home_workspace.set_start_swarm_status(
            level="idle",
            label="Swarm Idle",
            detail=(
                "Use Launch Review to run the guarded dry-run preflight first, "
                "then open the live review-channel lanes when the preflight is green."
            ),
            command_preview="No Start Swarm command has run yet.",
        )
        self.raw_bridge_text = self._make_readonly_panel(
            "Raw bridge.md content appears here.",
            wrap_lines=True,
            tooltip=(
                "Wrapped bridge snapshot from repo-visible markdown. This is the "
                "human-reading path, not a mystery button surface."
            ),
        )
        self.timeline_panel = TimelinePanel()
        self.workflow_header_bar = WorkflowHeaderBar()
        self.workflow_timeline_footer = WorkflowTimelineFooter()
        self.command_output = self._make_readonly_panel(
            "review-channel launcher and rollover command output appears here.",
            tooltip="Typed launcher command output from dry-run, live launch, and rollover.",
        )
        self.dev_log_text = self._make_readonly_panel(
            "High-level diagnostics events appear here.",
            tooltip="High-level diagnostics events and warnings for the desktop shell.",
        )
        self.activity_workspace = ActivityWorkspace()
        self.activity_workspace.set_start_swarm_status(
            status_level="idle",
            status_label="Swarm Idle",
            detail=(
                "No Launch Review chain has run yet. Use the visible action to run dry-run "
                "preflight first, then the live launch when the preflight is green."
            ),
            command_preview="No Start Swarm command has run yet.",
        )
        self._activity_text = self.activity_workspace.report_text
        self._activity_meta_label = self.activity_workspace.report_meta_label
        self._assist_text = self.activity_workspace.assist_text
        self._assist_meta_label = self.activity_workspace.assist_meta_label
        self.codex_activity_card = self.activity_workspace.codex_card
        self.cursor_activity_card = self.activity_workspace.cursor_card
        self.claude_activity_card = self.activity_workspace.claude_card
        self.operator_activity_card = self.activity_workspace.operator_card
        self.workbench_codex_card = AgentSummaryCard("Codex", role="Reviewer")
        self.workbench_operator_card = AgentSummaryCard("Operator", role="Bridge State")
        self.workbench_claude_card = AgentSummaryCard("Claude", role="Implementer")
        self.workbench_cursor_card = AgentSummaryCard("Cursor", role="Editor")

    def _create_analytics_widgets(self) -> None:
        self._analytics_text = self._make_readonly_panel(
            "Repo-visible review signals and any wired telemetry will appear here.",
            wrap_lines=True,
            tooltip=(
                "High-level repo pulse derived from the bridge, git status, CI, "
                "mutation, and phone-status artifacts."
            ),
        )
        self._analytics_repo_text = self._make_readonly_panel(
            "Working-tree status and hotspot paths will appear here.",
            wrap_lines=True,
            tooltip="Working-tree and hotspot summary derived from repo-owned git-status collectors.",
        )
        self._analytics_quality_text = self._make_readonly_panel(
            "Mutation, CI, warning, and approval health will appear here.",
            wrap_lines=True,
            tooltip="Mutation, CI, warning, and approval health derived from repo-owned collectors.",
        )
        self._analytics_phone_text = self._make_readonly_panel(
            "Phone relay and autonomy-control state will appear here.",
            wrap_lines=True,
            tooltip=(
                "Repo-owned phone-status projection used for iPhone-safe read surfaces "
                "and future push adapters."
            ),
        )

    def _create_collaboration_widgets(self) -> None:
        self.approval_panel = ApprovalQueuePanel()
        self.approval_panel.decision_requested.connect(self._on_approval_decision)
        self._approval_container = self.approval_panel
        self.conversation_panel = ConversationPanel()
        self.conversation_panel.post_requested.connect(self._on_conversation_post)
        self.task_board_panel = TaskBoardPanel()
        self.task_board_panel.ticket_selected.connect(self._on_ticket_selected)

    def _create_toolbar_controls(self) -> None:
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 100)
        self.threshold_spin.setValue(50)
        self.threshold_spin.setFixedWidth(60)
        self.threshold_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.threshold_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.threshold_spin.setToolTip(
            "Rollover threshold percentage used by the shared review-channel flow."
        )
        self.ack_wait_spin = QSpinBox()
        self.ack_wait_spin.setRange(1, 3600)
        self.ack_wait_spin.setValue(180)
        self.ack_wait_spin.setFixedWidth(60)
        self.ack_wait_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.ack_wait_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ack_wait_spin.setToolTip(
            "Seconds to wait for acknowledgements during rollover (minimum 1)."
        )
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(110)
        self.theme_combo.setToolTip(
            "Choose the active desktop theme. Use Theme Editor for deeper styling work."
        )
        for candidate in available_theme_ids():
            theme = resolve_theme(candidate)
            self.theme_combo.addItem(theme.display_name, theme.theme_id)
        self.theme_combo.currentIndexChanged.connect(self._change_theme)
        self.layout_combo = QComboBox()
        self.layout_combo.setFixedWidth(100)
        self.layout_combo.setToolTip("Choose how the same persistent panes are arranged.")
        for lid in available_layout_ids():
            desc = resolve_layout(lid)
            self.layout_combo.addItem(desc.display_name, desc.mode_id)
        layout_index = self.layout_combo.findData(self._layout_mode)
        if layout_index >= 0:
            self.layout_combo.setCurrentIndex(layout_index)
        self.layout_combo.currentIndexChanged.connect(self._change_layout)
        self.read_mode_combo = QComboBox()
        self.read_mode_combo.setFixedWidth(110)
        self.read_mode_combo.setToolTip(
            "Switch between simple and technical reading modes for summaries and footer text."
        )
        self.read_mode_combo.addItem("Simple", "simple")
        self.read_mode_combo.addItem("Technical", "technical")
        self.read_mode_combo.currentIndexChanged.connect(self._change_audience_mode)
        self.refresh_button = self._make_small_button("Refresh")
        self.refresh_button.setToolTip("Refresh the repo-visible snapshot now.")
        self.launch_dry_button = self._make_small_button("Dry")
        self.launch_dry_button.setToolTip(
            "Run the shared review-channel launcher in dry-run mode."
        )
        self.launch_live_button = self._make_small_button("Live")
        self.launch_live_button.setToolTip(
            "Launch the real review-channel flow through Terminal.app on macOS using the shared typed command path."
        )
        self.launch_live_button.setProperty("accentRole", "primary")
        self.rollover_button = self._make_small_button("Roll")
        self.rollover_button.setToolTip(
            "Request a guarded rollover through Terminal.app on macOS using the configured threshold and ACK wait."
        )
        self.rollover_button.setProperty("accentRole", "warning")
        self._command_button_defaults = {
            self.launch_dry_button: self.launch_dry_button.text(),
            self.launch_live_button: self.launch_live_button.text(),
            self.rollover_button: self.rollover_button.text(),
            self.home_workspace.audit_button: self.home_workspace.audit_button.text(),
            self.home_workspace.run_loop_button: self.home_workspace.run_loop_button.text(),
            self.home_workspace.home_dry_run_button: self.home_workspace.home_dry_run_button.text(),
            self.home_workspace.start_swarm_button: self.home_workspace.start_swarm_button.text(),
            self.activity_workspace.activity_audit_button: self.activity_workspace.activity_audit_button.text(),
            self.activity_workspace.activity_run_loop_button: self.activity_workspace.activity_run_loop_button.text(),
            self.activity_workspace.activity_dry_run_button: self.activity_workspace.activity_dry_run_button.text(),
            self.activity_workspace.activity_start_swarm_button: self.activity_workspace.activity_start_swarm_button.text(),
            self.activity_workspace.activity_ci_status_button: self.activity_workspace.activity_ci_status_button.text(),
            self.activity_workspace.activity_triage_button: self.activity_workspace.activity_triage_button.text(),
            self.activity_workspace.activity_process_audit_button: self.activity_workspace.activity_process_audit_button.text(),
            self.activity_workspace.assist_live_button: self.activity_workspace.assist_live_button.text(),
        }

    def _wire_ui_signals(self) -> None:
        self.refresh_button.clicked.connect(self.request_manual_refresh)
        self.launch_dry_button.clicked.connect(self.launch_dry_run)
        self.launch_live_button.clicked.connect(self.launch_live)
        self.rollover_button.clicked.connect(self.rollover_live)
        self.activity_workspace.report_button.clicked.connect(self.refresh_selected_report)
        self.activity_workspace.report_selector.currentIndexChanged.connect(
            self.refresh_selected_report
        )
        self.home_workspace.workflow_selector.currentIndexChanged.connect(
            self._sync_workflow_selector_from_home
        )
        self.activity_workspace.workflow_selector.currentIndexChanged.connect(
            self._sync_workflow_selector_from_activity
        )
        self.home_workspace.audit_button.clicked.connect(self.run_workflow_audit)
        self.home_workspace.run_loop_button.clicked.connect(self.run_selected_plan_loop)
        self.home_workspace.home_dry_run_button.clicked.connect(self.launch_dry_run)
        self.activity_workspace.activity_audit_button.clicked.connect(self.run_workflow_audit)
        self.activity_workspace.activity_run_loop_button.clicked.connect(
            self.run_selected_plan_loop
        )
        self.activity_workspace.activity_dry_run_button.clicked.connect(
            self.launch_dry_run
        )
        self.activity_workspace.activity_start_swarm_button.clicked.connect(
            self.start_swarm
        )
        self.activity_workspace.activity_ci_status_button.clicked.connect(
            self.show_ci_status
        )
        self.activity_workspace.activity_triage_button.clicked.connect(self.run_triage)
        self.activity_workspace.activity_process_audit_button.clicked.connect(
            self.run_process_audit
        )
        self.activity_workspace.assist_button.clicked.connect(self.generate_summary_draft)
        self.activity_workspace.assist_live_button.clicked.connect(
            self.generate_live_summary
        )
        self.home_workspace.dashboard_button.clicked.connect(self._open_dashboard_surface)
        self.home_workspace.start_swarm_button.clicked.connect(self.start_swarm)
        self.home_workspace.monitor_button.clicked.connect(self._open_monitor_surface)
        self.home_workspace.activity_button.clicked.connect(self._open_activity_surface)
        self.home_workspace.guide_button.clicked.connect(
            lambda: self._open_help_dialog("overview")
        )
        if HAS_THEME_EDITOR:
            self.theme_editor_btn = QPushButton("Theme Editor")
            self.theme_editor_btn.setObjectName("SmallActionButton")
            self.theme_editor_btn.setToolTip("Open the full theme editor")
            self.theme_editor_btn.clicked.connect(self._open_theme_editor)
            self.home_workspace.theme_button.clicked.connect(self._open_theme_editor)
        else:
            self.theme_editor_btn = None
        self.home_workspace.set_theme_editor_available(HAS_THEME_EDITOR)

    def _finalize_theme_and_modes(self, theme_id: str | None) -> None:
        self._theme_engine.theme_changed.connect(self._sync_theme_from_engine)
        if theme_id is not None and self._theme_engine.current_theme_id != theme_id:
            self._apply_theme(theme_id)
        else:
            self._sync_theme_from_engine()
        self._apply_workflow_preset(self._workflow_preset_id, announce=False)
        self._refresh_live_terminal_controls()

    def _build_window_shell(self) -> None:
        central = QWidget()
        central.setObjectName("RootWidget")
        self._root_layout = QVBoxLayout(central)
        self._root_layout.setContentsMargins(12, 8, 12, 8)
        self._root_layout.setSpacing(8)
        self._root_layout.addWidget(self._build_toolbar())
        self._content_widget = self._build_content_for_mode(self._layout_mode)
        self._root_layout.addWidget(self._content_widget, stretch=1)
        self.setCentralWidget(central)
        self._setup_menu_bar()
        self.setStatusBar(QStatusBar())
        self._apply_pending_layout_state()
        self._layout_state_ready = True
        self._persist_layout_state()

    def _start_polling_timer(self) -> None:
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.refresh_snapshot)
        self.poll_timer.start(2000)

    # ── Widget factories ──────────────────────────────────────

    def _make_readonly_panel(
        self,
        placeholder: str,
        *,
        wrap_lines: bool = False,
        tooltip: str | None = None,
    ) -> QPlainTextEdit:
        widget = QPlainTextEdit()
        widget.setObjectName("PanelRawText")
        widget.setReadOnly(True)
        widget.setPlaceholderText(placeholder)
        if wrap_lines:
            widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        if tooltip:
            widget.setToolTip(tooltip)
        return widget

    def _make_small_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("SmallActionButton")
        return btn

    # ── Logging helpers ──────────────────────────────────────────

    def _record_event(
        self,
        level: str,
        event: str,
        message: str,
        *,
        details: dict[str, object] | None = None,
    ) -> None:
        line = self.diagnostics.log(
            level=level,
            event=event,
            message=message,
            details=details,
        )
        self._append_dev_log(line + "\n")

    def _append_output(self, text: str) -> None:
        append_plain_text_preserving_scroll(self.command_output, text)

    def _append_dev_log(self, text: str) -> None:
        append_plain_text_preserving_scroll(self.dev_log_text, text)

    def closeEvent(self, event: object) -> None:
        self._persist_layout_state()
        if self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning:
            self._record_event(
                "WARNING",
                "window_close_while_busy",
                "Operator Console window closed while a command was still running",
                details={"pid": self._process.processId()},
            )
        else:
            self._record_event(
                "INFO",
                "window_close",
                "Operator Console window closed cleanly",
            )
        self.poll_timer.stop()
        super().closeEvent(event)


def run(
    repo_root: Path,
    *,
    diagnostics: OperatorConsoleDiagnostics | None = None,
    dev_log_enabled: bool = False,
    theme_id: str | None = None,
    layout_mode: str = DEFAULT_LAYOUT_ID,
    persist_layout_state: bool = True,
    layout_state_path: Path | None = None,
) -> int:  # pragma: no cover - manual UI path
    """Launch the optional PyQt6 Operator Console window."""
    diagnostics = diagnostics or OperatorConsoleDiagnostics.create(
        repo_root, enabled=False
    )
    if QApplication is None:
        diagnostics.log(
            level="ERROR",
            event="pyqt_missing",
            message="PyQt6 is not installed for the Operator Console UI",
            details={"repo_root": repo_root},
        )
        raise SystemExit(
            f"PyQt6 is not installed. Rerun `{preferred_launcher_command()}`, or "
            f"install it with `{manual_pyqt6_install_command()}` and rerun "
            f"`{manual_module_launch_command()}`."
        ) from IMPORT_ERROR

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.setApplicationName("VoiceTerm Operator Console")
    engine = get_engine()
    resolved_theme_id = resolve_theme(theme_id).theme_id if theme_id is not None else None
    if resolved_theme_id is not None:
        engine.apply_builtin_theme(resolved_theme_id)
        engine.save_current()
    else:
        engine.load_saved()
    app.setStyleSheet(engine.generate_stylesheet())

    window = OperatorConsoleWindow(
        repo_root,
        diagnostics=diagnostics,
        dev_log_enabled=dev_log_enabled,
        theme_id=resolved_theme_id,
        layout_mode=layout_mode,
        persist_layout_state=persist_layout_state,
        layout_state_path=layout_state_path,
    )
    window.show()
    return app.exec()
