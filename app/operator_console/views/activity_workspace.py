"""Activity workspace widget for the Operator Console.

Snap-to-grid layout: 3-column QGridLayout with agent summary cards in the
top row, data panels (reports / AI assist) spanning the middle, and a
guidance sidebar that keeps page actions up in the toolbar.
"""

from __future__ import annotations

from ..state.activity_assist import available_summary_draft_targets
from ..state.activity_reports import available_report_options
from .swarm_status_widgets import apply_swarm_status_widgets
from .widgets import AgentSummaryCard, compact_display_text, configure_compact_button

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object


class ActivityWorkspace(QWidget if _PYQT_AVAILABLE else object):
    """Composite Activity-tab surface with agent cards, actions, and drafts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # ── Agent summary cards ──────────────────────────────────
        self.codex_card = AgentSummaryCard("Codex", role="Reviewer")
        self.claude_card = AgentSummaryCard("Claude", role="Implementer")
        self.operator_card = AgentSummaryCard("Operator", role="Bridge State")

        # ── Data panels ──────────────────────────────────────────
        self.report_text = self._make_panel(
            "Selected human-readable report will appear here."
        )
        self.assist_text = self._make_panel(
            "Provider-targeted AI summary draft will appear here. "
            "This is staged text, not live execution."
        )

        # ── Report controls ──────────────────────────────────────
        self.report_selector = QComboBox()
        for option in available_report_options():
            self.report_selector.addItem(option.label, option.report_id)
        self.report_selector.setToolTip("Choose which report you want to read.")

        self.report_button = self._make_action_button(
            "Build", "Generate a human-readable summary for the selected report topic."
        )
        self.report_button.setProperty("accentRole", "primary")

        self.report_meta_label = QLabel(
            "Readable report from the current repo-visible snapshot."
        )
        self.report_meta_label.setObjectName("CardDetailLabel")
        self.report_meta_label.setWordWrap(True)

        # ── AI Assist controls ───────────────────────────────────
        self.assist_provider_selector = QComboBox()
        for target in available_summary_draft_targets():
            self.assist_provider_selector.addItem(target.label, target.provider_id)
        self.assist_provider_selector.setToolTip(
            "Choose which provider the staged AI summary draft should target."
        )

        self.assist_button = self._make_action_button(
            "Draft", "Generate a provider-targeted staged summary prompt."
        )
        self.assist_button.setProperty("accentRole", "primary")

        self.assist_meta_label = QLabel(
            "Draft from the selected report. Staged text only."
        )
        self.assist_meta_label.setObjectName("CardDetailLabel")
        self.assist_meta_label.setWordWrap(True)

        # ── Action buttons (compact) ─────────────────────────────
        self.activity_dry_run_button = self._make_small_button(
            "Dry Run", "Preview the review-channel launch without opening terminals."
        )
        self.activity_start_swarm_button = self._make_small_button(
            "Start Swarm", "Preflight first, then live launch via Terminal.app."
        )
        self.activity_start_swarm_button.setProperty("accentRole", "primary")
        self.activity_ci_status_button = self._make_small_button(
            "CI Status", "Run the repo-owned CI status surface."
        )
        self.activity_triage_button = self._make_small_button(
            "Triage", "Run the repo-owned triage surface."
        )
        self.activity_process_audit_button = self._make_small_button(
            "Process Audit", "Run strict host-side process audit."
        )
        self.activity_process_audit_button.setProperty("accentRole", "warning")
        self._quick_action_buttons = (
            self.activity_start_swarm_button,
            self.activity_dry_run_button,
            self.activity_ci_status_button,
            self.activity_triage_button,
            self.activity_process_audit_button,
        )

        # ── Swarm status (data display, not buttons) ─────────────
        self.swarm_status_dot = QLabel()
        self.swarm_status_dot.setObjectName("StatusIndicator")
        self.swarm_status_dot.setFixedSize(14, 14)
        self.swarm_status_dot.setProperty("statusLevel", "idle")

        self.swarm_status_label = QLabel("Swarm Idle")
        self.swarm_status_label.setObjectName("CardStatusLabel")
        self.swarm_status_label.setWordWrap(True)

        self.swarm_detail_label = QLabel(
            "Run Start Swarm to preflight first, then launch live only if green."
        )
        self.swarm_detail_label.setObjectName("CardDetailLabel")
        self.swarm_detail_label.setWordWrap(True)

        self.swarm_command_label = QLabel("Swarm command: idle")
        self.swarm_command_label.setObjectName("MutedLabel")
        self.swarm_command_label.setWordWrap(True)

        # ── Root grid layout ─────────────────────────────────────
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)

        # Row 0: Agent summary cards — 3 equal columns
        grid.addWidget(self.codex_card, 0, 0)
        grid.addWidget(self.operator_card, 0, 1)
        grid.addWidget(self.claude_card, 0, 2)

        # Row 1: Report panel (2 cols) + Swarm status card
        grid.addWidget(self._build_report_card(), 1, 0, 1, 2)
        grid.addWidget(self._build_swarm_card(), 1, 2)

        # Row 2: AI Assist panel (2 cols) + Actions card
        grid.addWidget(self._build_assist_card(), 2, 0, 1, 2)
        grid.addWidget(self._build_actions_card(), 2, 2)

        # Column and row proportions
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 2)
        grid.setRowStretch(0, 0)  # agent cards: fixed height
        grid.setRowStretch(1, 3)  # report + swarm: primary data
        grid.setRowStretch(2, 2)  # assist + actions: secondary data

        root.addLayout(grid)

    # ── Card builders ────────────────────────────────────────────

    def _build_report_card(self) -> QFrame:
        """Report data card: selector inline, text area dominates."""
        card = QFrame()
        card.setObjectName("LaneCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        self.report_title_label = QLabel("Reports")
        self.report_title_label.setObjectName("LaneAgentName")
        layout.addWidget(self.report_title_label)
        self.report_intro_label = QLabel(
            "Script-derived view of the current review snapshot."
        )
        self.report_intro_label.setObjectName("CardDetailLabel")
        self.report_intro_label.setWordWrap(True)
        layout.addWidget(self.report_intro_label)

        # Inline control strip: selector + compact build button
        controls = QHBoxLayout()
        controls.setSpacing(6)
        controls.addWidget(self.report_selector, stretch=1)
        controls.addWidget(self.report_button)
        layout.addLayout(controls)
        layout.addWidget(self.report_meta_label)

        # Data area
        layout.addWidget(self.report_text, stretch=1)
        return card

    def _build_swarm_card(self) -> QFrame:
        """Swarm status as a data-first card: indicator + labels."""
        card = QFrame()
        card.setObjectName("LaneCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        self.swarm_title_label = QLabel("Swarm")
        self.swarm_title_label.setObjectName("LaneAgentName")
        layout.addWidget(self.swarm_title_label)
        self.swarm_intro_label = QLabel(
            "Live health of the dry-run and launch path."
        )
        self.swarm_intro_label.setObjectName("CardDetailLabel")
        self.swarm_intro_label.setWordWrap(True)
        layout.addWidget(self.swarm_intro_label)

        # Status indicator row
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        status_row.addWidget(
            self.swarm_status_dot, alignment=Qt.AlignmentFlag.AlignTop
        )
        status_row.addWidget(self.swarm_status_label, stretch=1)
        layout.addLayout(status_row)

        layout.addWidget(self.swarm_detail_label)
        layout.addWidget(self.swarm_command_label)
        layout.addStretch(1)
        return card

    def _build_assist_card(self) -> QFrame:
        """AI Assist data card: provider selector inline, draft text dominates."""
        card = QFrame()
        card.setObjectName("LaneCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        self.assist_title_label = QLabel("Draft")
        self.assist_title_label.setObjectName("LaneAgentName")
        layout.addWidget(self.assist_title_label)
        self.assist_intro_label = QLabel(
            "Provider-targeted staged draft output only."
        )
        self.assist_intro_label.setObjectName("CardDetailLabel")
        self.assist_intro_label.setWordWrap(True)
        layout.addWidget(self.assist_intro_label)

        # Inline control strip
        controls = QHBoxLayout()
        controls.setSpacing(6)
        controls.addWidget(self.assist_provider_selector, stretch=1)
        controls.addWidget(self.assist_button)
        layout.addLayout(controls)
        layout.addWidget(self.assist_meta_label)

        # Data area
        layout.addWidget(self.assist_text, stretch=1)
        return card

    def _build_actions_card(self) -> QFrame:
        """Explain how Activity should be used without adding button clutter."""
        card = QFrame()
        card.setObjectName("LaneCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        self.actions_title_label = QLabel("Workflow")
        self.actions_title_label.setObjectName("LaneAgentName")
        layout.addWidget(self.actions_title_label)

        self.actions_intro_label = QLabel(
            "Read the report, scan the draft, then decide the next typed action."
        )
        self.actions_intro_label.setObjectName("CardDetailLabel")
        self.actions_intro_label.setWordWrap(True)
        layout.addWidget(self.actions_intro_label)

        self.toolbar_hint_label = QLabel(
            "Actions stay in the toolbar above."
        )
        self.toolbar_hint_label.setObjectName("CardStatusLabel")
        self.toolbar_hint_label.setWordWrap(True)
        layout.addWidget(self.toolbar_hint_label)

        self.next_step_hint_label = QLabel(
            "Switch to Workbench or Monitor when you need raw bridge, launcher, or diagnostics output."
        )
        self.next_step_hint_label.setObjectName("CardDetailLabel")
        self.next_step_hint_label.setWordWrap(True)
        layout.addWidget(self.next_step_hint_label)

        layout.addStretch(1)
        return card

    # ── Widget factories ─────────────────────────────────────────

    def _make_panel(self, placeholder: str) -> QPlainTextEdit:
        widget = QPlainTextEdit()
        widget.setObjectName("PanelRawText")
        widget.setReadOnly(True)
        widget.setPlaceholderText(placeholder)
        widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        return widget

    def _make_action_button(self, label: str, tooltip: str) -> QPushButton:
        button = QPushButton(label)
        button.setToolTip(tooltip)
        return configure_compact_button(button)

    def _make_small_button(self, label: str, tooltip: str) -> QPushButton:
        button = QPushButton(label)
        button.setToolTip(tooltip)
        return configure_compact_button(button)

    # ── Public state updates ─────────────────────────────────────

    def set_audience_mode(self, mode: str) -> None:
        """Switch the Activity workspace between simple and technical framing."""
        technical_mode = mode == "technical"
        self.report_title_label.setText(
            "Report Digest" if technical_mode else "Reports"
        )
        self.report_intro_label.setText(
            "Dense script-derived digest from the current repo-visible review state."
            if technical_mode
            else "Script-derived view of the current review snapshot."
        )
        self.assist_title_label.setText(
            "Stage Prompt" if technical_mode else "Draft"
        )
        self.assist_intro_label.setText(
            "Prompt staging only. Keep the report above as the primary source of truth."
            if technical_mode
            else "Provider-targeted staged draft output only."
        )
        self.swarm_title_label.setText(
            "Launch State" if technical_mode else "Swarm"
        )
        self.swarm_intro_label.setText(
            "Typed launch path status only: preflight, gating, and last command preview."
            if technical_mode
            else "Live health of the dry-run and launch path."
        )
        self.actions_title_label.setText(
            "Operator Flow" if technical_mode else "Workflow"
        )
        self.actions_intro_label.setText(
            "Read the digest, inspect raw output in Monitor, then act through the small toolbar controls."
            if technical_mode
            else "Read the report, scan the draft, then decide the next typed action."
        )
        self.toolbar_hint_label.setText(
            "Toolbar flow: Refresh | Dry | Live | Roll"
            if technical_mode
            else "Actions stay in the toolbar above."
        )
        self.next_step_hint_label.setText(
            "Monitor carries raw bridge, command, and diagnostics output when the digest is not enough."
            if technical_mode
            else "Switch to Workbench or Monitor when you need raw bridge, launcher, or diagnostics output."
        )

    def set_start_swarm_status(
        self,
        *,
        status_level: str,
        status_label: str,
        detail: str,
        command_preview: str | None = None,
    ) -> None:
        """Mirror Start Swarm state in the swarm status card."""
        apply_swarm_status_widgets(
            dot=self.swarm_status_dot,
            status_label=self.swarm_status_label,
            detail_label=self.swarm_detail_label,
            command_label=self.swarm_command_label,
            level=status_level,
            label=status_label,
            detail=detail,
            command_preview=command_preview,
        )
