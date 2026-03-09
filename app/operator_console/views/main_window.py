"""PyQt6 UI for the optional review-channel Operator Console.

This module is the slim orchestrator — it wires together widget creation,
page layout (ui_pages), data refresh (ui_refresh), and scroll helpers
(ui_scroll) without containing any of that logic itself.
"""

from __future__ import annotations

from pathlib import Path

from ..state.command_builder import (
    OPERATOR_DECISION_MODULE,
    build_operator_decision_command,
    parse_operator_decision_report,
    terminal_app_live_support_detail,
    terminal_app_live_supported,
)
from ..state.models import ApprovalRequest
from ..logging_support import OperatorConsoleDiagnostics
from ..theme import (
    available_theme_ids,
    get_engine,
    resolve_theme,
)
from .help_dialog import OperatorHelpDialog
from .home_workspace import HomeWorkspace
from .activity_workspace import ActivityWorkspace
from .approval_panel import ApprovalQueuePanel
from .ui_layouts import (
    DEFAULT_LAYOUT_ID,
    DEFAULT_WORKBENCH_PRESET_ID,
    available_layout_ids,
    resolve_layout,
)

try:
    from ..theme.theme_editor import ThemeEditorDialog as _ThemeEditorDialog
    _HAS_THEME_EDITOR = True
except ImportError:
    _HAS_THEME_EDITOR = False
from .ui_pages import PageBuilderMixin
from .ui_refresh import RefreshMixin
from .ui_scroll import append_plain_text_preserving_scroll, replace_plain_text_preserving_scroll
from .widgets import AgentSummaryCard, KeyValuePanel, StatusIndicator

try:
    from PyQt6.QtCore import QProcess, QTimer, Qt
    from PyQt6.QtGui import QAction, QActionGroup
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
    PageBuilderMixin, RefreshMixin, QMainWindow
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
    ) -> None:
        super().__init__()
        self.repo_root = repo_root
        self.diagnostics = diagnostics
        self.dev_log_enabled = dev_log_enabled
        self.theme_id: str | None = None
        self._layout_mode = resolve_layout(layout_mode).mode_id
        self._workbench_preset = DEFAULT_WORKBENCH_PRESET_ID
        self._process: QProcess | None = None
        self._active_command_context: dict[str, object] | None = None
        self._active_command_stdout = ""
        self._active_command_stderr = ""
        self._last_snapshot_digest: str | None = None
        self._theme_editor_dialog: QDialog | None = None
        self._theme_engine = get_engine()
        self._dynamic_theme_combo_data = "__active_theme__"
        self._help_dialog: QDialog | None = None
        self._audience_mode = "simple"
        self._live_terminal_supported = terminal_app_live_supported()
        self._live_terminal_support_detail = terminal_app_live_support_detail()

        self.setWindowTitle("VoiceTerm Operator Console")
        self.resize(1720, 1040)

        # ── Persistent data widgets ──────────────────────────────
        # These survive layout switches — they get reparented, never
        # destroyed, so scroll position and text content are preserved.

        # Toolbar status dots
        self.codex_dot = StatusIndicator()
        self.claude_dot = StatusIndicator()
        self.operator_dot = StatusIndicator()

        # Lane dots (used inside lane card headers, separate from toolbar)
        self._codex_lane_dot = StatusIndicator()
        self._claude_lane_dot = StatusIndicator()
        self._operator_lane_dot = StatusIndicator()

        # Structured KV panels (the centerpiece)
        self.codex_panel = KeyValuePanel("Codex Bridge Monitor")
        self.claude_panel = KeyValuePanel("Claude Bridge Monitor")
        self.operator_panel = KeyValuePanel("Operator Bridge State")
        self.codex_session_text = self._make_readonly_panel(
            "Codex session trace and agent-registry activity will appear here.",
            tooltip=(
                "Reviewer session surface. Prefers live review-channel session "
                "trace logs when available and falls back to the bridge/registry summary."
            ),
        )
        self.claude_session_text = self._make_readonly_panel(
            "Claude session trace and agent-registry activity will appear here.",
            tooltip=(
                "Implementer session surface. Prefers live review-channel session "
                "trace logs when available and falls back to the bridge/registry summary."
            ),
        )

        # Monitor panels
        self.home_workspace = HomeWorkspace()
        self.home_workspace.set_start_swarm_status(
            level="idle",
            label="Swarm Idle",
            detail=(
                "Run Start Swarm to execute the guarded dry-run preflight first, "
                "then launch the live review-channel swarm when the preflight is green."
            ),
            command_preview="No Start Swarm command has run yet.",
        )
        self.raw_bridge_text = self._make_readonly_panel(
            "Raw code_audit.md content appears here.",
            wrap_lines=True,
            tooltip=(
                "Wrapped bridge snapshot from repo-visible markdown. This is the "
                "human-reading path, not a mystery button surface."
            ),
        )
        self.command_output = self._make_readonly_panel(
            "review-channel launcher and rollover command output appears here.",
            tooltip="Typed launcher command output from dry-run, live launch, and rollover.",
        )
        self.dev_log_text = self._make_readonly_panel(
            "High-level diagnostics events appear here.",
            tooltip="High-level diagnostics events and warnings for the desktop shell.",
        )

        # Activity workspace (agent summaries, quick actions, staged drafts)
        self.activity_workspace = ActivityWorkspace()
        self.activity_workspace.set_start_swarm_status(
            status_level="idle",
            status_label="Swarm Idle",
            detail=(
                "No Start Swarm chain has run yet. Use the quick action to run dry-run "
                "preflight first, then the live launch when the preflight is green."
            ),
            command_preview="No Start Swarm command has run yet.",
        )
        self._activity_text = self.activity_workspace.report_text
        self._activity_meta_label = self.activity_workspace.report_meta_label
        self._assist_text = self.activity_workspace.assist_text
        self._assist_meta_label = self.activity_workspace.assist_meta_label
        self.codex_activity_card = self.activity_workspace.codex_card
        self.claude_activity_card = self.activity_workspace.claude_card
        self.operator_activity_card = self.activity_workspace.operator_card
        self.workbench_codex_card = AgentSummaryCard("Codex", role="Reviewer")
        self.workbench_operator_card = AgentSummaryCard("Operator", role="Bridge State")
        self.workbench_claude_card = AgentSummaryCard("Claude", role="Implementer")

        # Analytics text (metrics dashboard)
        self._analytics_text = self._make_readonly_panel(
            "Repo-visible review signals and any wired telemetry will appear here.",
            wrap_lines=True,
            tooltip=(
                "High-level repo pulse derived from the bridge, git status, CI, mutation, and phone-status artifacts."
            ),
        )
        self._analytics_repo_text = self._make_readonly_panel(
            "Working-tree status and hotspot paths will appear here.",
            wrap_lines=True,
            tooltip=(
                "Working-tree and hotspot summary derived from repo-owned git-status collectors."
            ),
        )
        self._analytics_quality_text = self._make_readonly_panel(
            "Mutation, CI, warning, and approval health will appear here.",
            wrap_lines=True,
            tooltip=(
                "Mutation, CI, warning, and approval health derived from repo-owned collectors."
            ),
        )
        self._analytics_phone_text = self._make_readonly_panel(
            "Phone relay and autonomy-control state will appear here.",
            wrap_lines=True,
            tooltip=(
                "Repo-owned phone-status projection used for iPhone-safe read surfaces and future push adapters."
            ),
        )

        # Approval queue panel (self-contained widget with detail pane)
        self.approval_panel = ApprovalQueuePanel()
        self.approval_panel.decision_requested.connect(self._on_approval_decision)
        self._approval_container = self.approval_panel

        # ── Toolbar settings ─────────────────────────────────────

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
        self.layout_combo.setToolTip(
            "Choose how the same persistent panes are arranged."
        )
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

        # Action buttons (compact, transparent)
        self.refresh_button = self._make_small_button("Refresh")
        self.refresh_button.setToolTip("Refresh the repo-visible snapshot now.")
        self.refresh_button.clicked.connect(self.request_manual_refresh)
        self.launch_dry_button = self._make_small_button("Dry")
        self.launch_dry_button.setToolTip(
            "Run the shared review-channel launcher in dry-run mode."
        )
        self.launch_dry_button.clicked.connect(self.launch_dry_run)
        self.launch_live_button = self._make_small_button("Live")
        self.launch_live_button.setToolTip(
            "Launch the real review-channel flow through Terminal.app on macOS using the shared typed command path."
        )
        self.launch_live_button.setProperty("accentRole", "primary")
        self.launch_live_button.clicked.connect(self.launch_live)
        self.rollover_button = self._make_small_button("Roll")
        self.rollover_button.setToolTip(
            "Request a guarded rollover through Terminal.app on macOS using the configured threshold and ACK wait."
        )
        self.rollover_button.setProperty("accentRole", "warning")
        self.rollover_button.clicked.connect(self.rollover_live)
        self._command_button_defaults = {
            self.launch_dry_button: self.launch_dry_button.text(),
            self.launch_live_button: self.launch_live_button.text(),
            self.rollover_button: self.rollover_button.text(),
        }
        self._swarm_button_defaults = {
            self.home_workspace.start_swarm_button: self.home_workspace.start_swarm_button.text(),
            self.activity_workspace.activity_start_swarm_button: (
                self.activity_workspace.activity_start_swarm_button.text()
            ),
        }
        self._activity_command_buttons = [
            self.activity_workspace.activity_start_swarm_button,
            self.activity_workspace.activity_dry_run_button,
            self.activity_workspace.activity_ci_status_button,
            self.activity_workspace.activity_triage_button,
            self.activity_workspace.activity_process_audit_button,
        ]
        self.activity_workspace.report_button.clicked.connect(
            self.refresh_selected_report
        )
        self.activity_workspace.report_selector.currentIndexChanged.connect(
            self.refresh_selected_report
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
        self.activity_workspace.activity_triage_button.clicked.connect(
            self.run_triage
        )
        self.activity_workspace.activity_process_audit_button.clicked.connect(
            self.run_process_audit
        )
        self.activity_workspace.assist_button.clicked.connect(
            self.generate_summary_draft
        )
        self.home_workspace.dashboard_button.clicked.connect(self._open_dashboard_surface)
        self.home_workspace.start_swarm_button.clicked.connect(self.start_swarm)
        self.home_workspace.monitor_button.clicked.connect(self._open_monitor_surface)
        self.home_workspace.activity_button.clicked.connect(self._open_activity_surface)
        self.home_workspace.start_swarm_button.setToolTip(
            "Run dry-run preflight first, then launch the live review-channel swarm through Terminal.app on macOS."
        )
        self.activity_workspace.activity_start_swarm_button.setToolTip(
            "Run dry-run preflight first, then launch the live review-channel swarm through Terminal.app on macOS."
        )
        self.home_workspace.guide_button.clicked.connect(
            lambda: self._open_help_dialog("overview")
        )

        # Theme editor button (opens the full theme editor dialog)
        if _HAS_THEME_EDITOR:
            self.theme_editor_btn = QPushButton("Theme Editor")
            self.theme_editor_btn.setObjectName("SmallActionButton")
            self.theme_editor_btn.setToolTip("Open the full theme editor")
            self.theme_editor_btn.clicked.connect(self._open_theme_editor)
            self.home_workspace.theme_button.clicked.connect(self._open_theme_editor)
        else:
            self.theme_editor_btn = None
        self.home_workspace.set_theme_editor_available(_HAS_THEME_EDITOR)

        self._theme_engine.theme_changed.connect(self._sync_theme_from_engine)
        if theme_id is not None and self._theme_engine.current_theme_id != theme_id:
            self._apply_theme(theme_id)
        else:
            self._sync_theme_from_engine()
        self._refresh_live_terminal_controls()

        # ── Assemble: toolbar + content ──────────────────────────

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

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.refresh_snapshot)
        self.poll_timer.start(2000)

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

    def _setup_menu_bar(self) -> None:
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(True)

        run_menu = menu_bar.addMenu("&Run")
        for label, handler in [
            ("Refresh Snapshot", self.request_manual_refresh),
            ("Dry Run", self.launch_dry_run),
            ("Live Launch", self.launch_live),
            ("Start Swarm", self.start_swarm),
            ("Rollover", self.rollover_live),
            ("CI Status", self.show_ci_status),
            ("Triage", self.run_triage),
            ("Process Audit", self.run_process_audit),
        ]:
            action = QAction(label, self)
            action.triggered.connect(handler)
            run_menu.addAction(action)

        view_menu = menu_bar.addMenu("&View")
        read_menu = view_menu.addMenu("Read Mode")
        read_group = QActionGroup(self)
        read_group.setExclusive(True)
        for mode_id in ("simple", "technical"):
            action = QAction(mode_id.title(), self)
            action.setCheckable(True)
            action.setChecked(mode_id == self.read_mode_combo.currentData())
            action.triggered.connect(
                lambda checked=False, value=mode_id: self._set_combo_data(
                    self.read_mode_combo,
                    value,
                )
            )
            read_group.addAction(action)
            read_menu.addAction(action)

        layout_menu = view_menu.addMenu("Layout")
        layout_group = QActionGroup(self)
        layout_group.setExclusive(True)
        for lid in available_layout_ids():
            desc = resolve_layout(lid)
            action = QAction(desc.display_name, self)
            action.setCheckable(True)
            action.setChecked(lid == self._layout_mode)
            action.triggered.connect(
                lambda checked=False, value=lid: self._set_combo_data(
                    self.layout_combo,
                    value,
                )
            )
            layout_group.addAction(action)
            layout_menu.addAction(action)

        theme_menu = menu_bar.addMenu("&Theme")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        current_theme_id = self.theme_combo.currentData()
        for theme_id in available_theme_ids():
            theme = resolve_theme(theme_id)
            action = QAction(theme.display_name, self)
            action.setCheckable(True)
            action.setChecked(theme_id == current_theme_id)
            action.triggered.connect(
                lambda checked=False, value=theme_id: self._set_combo_data(
                    self.theme_combo,
                    value,
                )
            )
            theme_group.addAction(action)
            theme_menu.addAction(action)

        if getattr(self, "theme_editor_btn", None) is not None:
            theme_menu.addSeparator()
            theme_editor_action = QAction("Open Theme Editor", self)
            theme_editor_action.triggered.connect(self._open_theme_editor)
            theme_menu.addAction(theme_editor_action)

        settings_menu = menu_bar.addMenu("&Settings")
        threshold_menu = settings_menu.addMenu("Threshold")
        threshold_group = QActionGroup(self)
        threshold_group.setExclusive(True)
        for value in (25, 50, 75):
            action = QAction(f"{value}%", self)
            action.setCheckable(True)
            action.setChecked(value == self.threshold_spin.value())
            action.triggered.connect(
                lambda checked=False, current=value: self.threshold_spin.setValue(current)
            )
            threshold_group.addAction(action)
            threshold_menu.addAction(action)

        ack_menu = settings_menu.addMenu("ACK Wait")
        ack_group = QActionGroup(self)
        ack_group.setExclusive(True)
        for value in (60, 180, 300):
            action = QAction(f"{value}s", self)
            action.setCheckable(True)
            action.setChecked(value == self.ack_wait_spin.value())
            action.triggered.connect(
                lambda checked=False, current=value: self.ack_wait_spin.setValue(current)
            )
            ack_group.addAction(action)
            ack_menu.addAction(action)

        help_menu = menu_bar.addMenu("&Help")
        guide_action = QAction("Operator Guide", self)
        guide_action.triggered.connect(lambda: self._open_help_dialog("overview"))
        help_menu.addAction(guide_action)

        controls_action = QAction("Controls Reference", self)
        controls_action.triggered.connect(lambda: self._open_help_dialog("controls"))
        help_menu.addAction(controls_action)

        theme_help_action = QAction("Theme Notes", self)
        theme_help_action.triggered.connect(lambda: self._open_help_dialog("theme"))
        help_menu.addAction(theme_help_action)

        mobile_help_action = QAction("Mobile Relay", self)
        mobile_help_action.triggered.connect(lambda: self._open_help_dialog("mobile"))
        help_menu.addAction(mobile_help_action)

        developer_menu = menu_bar.addMenu("&Developer")
        developer_notes_action = QAction("How This Runs", self)
        developer_notes_action.triggered.connect(
            lambda: self._open_help_dialog("developer")
        )
        developer_menu.addAction(developer_notes_action)

        refresh_action = QAction("Refresh Snapshot", self)
        refresh_action.triggered.connect(self.request_manual_refresh)
        developer_menu.addAction(refresh_action)

    def _open_dashboard_surface(self) -> None:
        self._navigate_primary_surface("dashboard")

    def _open_monitor_surface(self) -> None:
        self._navigate_primary_surface("monitor")

    def _open_activity_surface(self) -> None:
        self._navigate_primary_surface("activity")

    def _set_combo_data(self, combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _open_help_dialog(self, topic_id: str) -> None:
        if self._help_dialog is None:
            dialog = OperatorHelpDialog(self)
            dialog.setModal(False)
            dialog.finished.connect(lambda *_: self._on_help_dialog_closed())
            self._help_dialog = dialog
        else:
            dialog = self._help_dialog

        dialog.show_topic(topic_id)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        self.statusBar().showMessage("Operator guide opened", 3000)

    def _on_help_dialog_closed(self) -> None:
        self._help_dialog = None
        self.statusBar().showMessage("Operator guide closed", 3000)

    def _open_theme_editor(self) -> None:
        """Open the full theme editor dialog."""
        if self._theme_editor_dialog is None:
            dialog = _ThemeEditorDialog(self)
            dialog.setModal(False)
            dialog.finished.connect(lambda *_: self._on_theme_editor_closed())
            self._theme_editor_dialog = dialog
        else:
            dialog = self._theme_editor_dialog

        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        self.statusBar().showMessage("Theme editor opened", 3000)

    def _on_theme_editor_closed(self) -> None:
        """Clear the cached dialog reference after the editor closes."""
        self._theme_editor_dialog = None
        self.statusBar().showMessage("Theme editor closed", 3000)

    def _refresh_live_terminal_controls(self) -> None:
        """Keep Terminal.app-only controls aligned with platform support."""
        if self._live_terminal_supported:
            return

        detail = self._live_terminal_support_detail
        for button in (
            self.launch_live_button,
            self.rollover_button,
            self.home_workspace.start_swarm_button,
            self.activity_workspace.activity_start_swarm_button,
        ):
            button.setEnabled(False)
            button.setToolTip(detail)
        self._set_start_swarm_status(
            swarm_level="stale",
            swarm_label="Swarm Live-Gated",
            swarm_detail=detail,
            command_preview=(
                "Use Launch Dry Run to execute the review-channel preflight "
                "without opening Terminal.app sessions."
            ),
        )

    def _set_command_controls_busy(self, busy: bool, *, label: str | None = None) -> None:
        """Expose command progress directly on the toolbar controls."""
        for button, default_text in self._command_button_defaults.items():
            button.setEnabled(not busy)
            if not busy:
                button.setText(default_text)

        for button, default_text in getattr(self, "_swarm_button_defaults", {}).items():
            button.setEnabled(not busy)
            if not busy:
                button.setText(default_text)

        for button in getattr(self, "_activity_command_buttons", []):
            button.setEnabled(not busy)

        if busy:
            if label is None:
                label = "Running..."
            self.launch_live_button.setText(label)
            if label.startswith("Swarm"):
                for button in getattr(self, "_swarm_button_defaults", {}):
                    button.setText(label)
            return

        self._refresh_live_terminal_controls()

    def record_decision(
        self,
        decision: str,
        *,
        approval: ApprovalRequest | None = None,
        note: str = "",
    ) -> None:
        """Route approval actions through a typed repo-owned command path."""
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
        """Handle a decision from the ApprovalQueuePanel signal."""
        if not isinstance(approval, ApprovalRequest):
            return
        self.record_decision(decision, approval=approval, note=note)

    def _describe_command(self, command: list[str]) -> str:
        """Expose approval-routing commands with operator-facing labels."""
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
        return RefreshMixin._describe_command(self, command)

    def _on_process_finished(self, exit_code: int, exit_status: object) -> None:
        active_context = dict(self._active_command_context or {})
        stdout = self._active_command_stdout
        stderr = self._active_command_stderr

        RefreshMixin._on_process_finished(self, exit_code, exit_status)

        if active_context.get("flow") != "operator_decision":
            return

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
            "ERROR" if exit_code else "WARNING",
            "operator_decision_failed",
            "Typed operator decision command did not report success",
            details={
                "decision": decision,
                "packet_id": packet_id,
                "exit_code": exit_code,
            },
        )
        self.statusBar().showMessage(message)

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
            "PyQt6 is not installed. Rerun `./scripts/operator_console.sh`, or "
            "install it with `python3 -m pip install PyQt6` and rerun "
            "`python3 app/operator_console/run.py`."
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
    )
    window.show()
    return app.exec()
