"""Start/home workspace for the Operator Console.

The home surface is read-first and asymmetric on purpose: one primary
overview panel on the left, a narrow signal rail on the right, and the
toolbar owning the real actions.
"""

from __future__ import annotations

from ..state.presentation_state import SystemBannerState
from .swarm_status_widgets import apply_swarm_status_widgets
from .widgets import compact_display_text

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object

class HomeWorkspace(QWidget if _PYQT_AVAILABLE else object):
    """Guided entry surface for operators before they dive into raw panes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_navigation_buttons()
        self._init_health_widgets()
        self._init_swarm_widgets()
        self._init_badges()
        self._init_digest_widgets()
        self._build_root_layout()

    def _init_navigation_buttons(self) -> None:
        # ── Navigation buttons (compact) ─────────────────────────
        self.dashboard_button = QPushButton("Dashboard")
        self.start_swarm_button = QPushButton("Start Swarm")
        self.monitor_button = QPushButton("Monitor")
        self.activity_button = QPushButton("Reports")
        self.theme_button = QPushButton("Theme")
        self.guide_button = QPushButton("Guide")
        self._nav_buttons = (
            self.dashboard_button,
            self.start_swarm_button,
            self.monitor_button,
            self.activity_button,
            self.theme_button,
            self.guide_button,
        )
        for button in self._nav_buttons:
            button.setObjectName("SmallActionButton")

        self.dashboard_button.setProperty("accentRole", "primary")
        self.start_swarm_button.setProperty("accentRole", "primary")
        self.guide_button.setProperty("accentRole", "primary")
        self.theme_button.setProperty("accentRole", "warning")

        self.dashboard_button.setToolTip("Jump into the live lane dashboard.")
        self.start_swarm_button.setToolTip(
            "Run the guarded Start Swarm path: review-channel dry-run preflight first, then live launch when green."
        )
        self.monitor_button.setToolTip("Jump into bridge, launcher, and diagnostics monitors.")
        self.activity_button.setToolTip("Jump into the human-readable report workspace.")
        self.theme_button.setToolTip("Open the theme editor workbench.")
        self.guide_button.setToolTip("Open the in-app guide and developer notes.")

    def _init_health_widgets(self) -> None:
        # ── Health status ────────────────────────────────────────
        self.health_dot = QLabel()
        self.health_dot.setObjectName("StatusIndicator")
        self.health_dot.setFixedSize(14, 14)
        self.health_dot.setProperty("statusLevel", "idle")

        self._primary_title = QLabel("System Health")
        self._primary_title.setObjectName("LaneAgentName")

        self.health_label = QLabel("Waiting For Snapshot")
        self.health_label.setObjectName("LaneAgentName")
        self.detail_label = QLabel("The latest repo-visible state will appear here.")
        self.detail_label.setObjectName("CardDetailLabel")
        self.detail_label.setWordWrap(True)

        self.agent_summary = QLabel("No lanes detected yet.")
        self.agent_summary.setObjectName("CardStatusLabel")
        self.agent_summary.setWordWrap(True)

    def _init_swarm_widgets(self) -> None:
        # ── Swarm status ─────────────────────────────────────────
        self.start_swarm_dot = QLabel()
        self.start_swarm_dot.setObjectName("StatusIndicator")
        self.start_swarm_dot.setFixedSize(14, 14)
        self.start_swarm_dot.setProperty("statusLevel", "idle")

        self.start_swarm_label = QLabel("Swarm Idle")
        self.start_swarm_label.setObjectName("CardStatusLabel")
        self.start_swarm_label.setWordWrap(True)
        self.start_swarm_detail_label = QLabel(
            "Run Start Swarm to preflight first, then launch live only if green."
        )
        self.start_swarm_detail_label.setObjectName("CardDetailLabel")
        self.start_swarm_detail_label.setWordWrap(True)
        self.start_swarm_command_label = self._make_badge("Swarm command: idle")
        self.start_swarm_command_label.setToolTip(
            "Most recent Start Swarm command preview."
        )

    def _init_badges(self) -> None:
        # ── Badges ───────────────────────────────────────────────
        self.mode_badge = self._make_badge("Read: Simple")
        self.review_mode_badge = self._make_badge("Mode: markdown-only")
        self.approvals_badge = self._make_badge("Approvals: 0")
        self.risk_badge = self._make_badge("Risk: Unknown")
        self.confidence_badge = self._make_badge("Confidence: Unknown")

    def _init_digest_widgets(self) -> None:
        # ── Data card labels ─────────────────────────────────────
        self.explainer_title = QLabel("Repo")
        self.explainer_title.setObjectName("SectionHeaderLabel")
        self.explainer_body = QLabel(
            "Branch, dirty state, and hotspot paths will appear here."
        )
        self.explainer_body.setObjectName("CardDetailLabel")
        self.explainer_body.setWordWrap(True)

        self.overview_title = QLabel("Snapshot")
        self.overview_title.setObjectName("SectionHeaderLabel")
        self.overview_body = QLabel("No overview report yet.")
        self.overview_body.setObjectName("CardDetailLabel")
        self.overview_body.setWordWrap(True)

        self.next_step_title = QLabel("Quality")
        self.next_step_title.setObjectName("SectionHeaderLabel")
        self.next_step_body = QLabel(
            "Warnings, approvals, mutation, and CI health will appear here."
        )
        self.next_step_body.setObjectName("CardDetailLabel")
        self.next_step_body.setWordWrap(True)

        self.launchpad_title = QLabel("Relay")
        self.launchpad_title.setObjectName("SectionHeaderLabel")
        self.launchpad_body = QLabel(
            "Phone relay state will appear here."
        )
        self.launchpad_body.setObjectName("CardDetailLabel")
        self.launchpad_body.setWordWrap(True)
        self.recommended_step_label = QLabel(
            "Next: refresh to get started."
        )
        self.recommended_step_label.setObjectName("CardDetailLabel")
        self.recommended_step_label.setWordWrap(True)
        self._digest_labels = (
            self.explainer_body,
            self.overview_body,
            self.next_step_body,
            self.launchpad_body,
            self.recommended_step_label,
        )

    def _build_root_layout(self) -> None:
        # ── Build split grid ─────────────────────────────────────
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)

        grid.addWidget(self._build_overview_card(), 0, 0, 2, 1)
        grid.addWidget(self._build_nav_card(), 0, 1)
        grid.addWidget(
            self._build_info_card(self.next_step_title, self.next_step_body),
            1,
            1,
        )
        grid.addWidget(
            self._build_info_card(self.explainer_title, self.explainer_body),
            2,
            0,
        )
        grid.addWidget(
            self._build_info_card(self.launchpad_title, self.launchpad_body),
            2,
            1,
        )

        grid.setColumnStretch(0, 5)
        grid.setColumnStretch(1, 3)
        grid.setRowStretch(0, 2)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 2)

        root.addLayout(grid)

    # ── Card builders ────────────────────────────────────────────

    def _build_overview_card(self) -> QFrame:
        """Primary left-hand overview surface with dense operational context."""
        card = QFrame()
        card.setObjectName("LaneCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        layout.addWidget(self._primary_title)

        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        status_row.addWidget(self.health_dot, alignment=Qt.AlignmentFlag.AlignTop)
        status_row.addWidget(self.health_label, stretch=1)
        status_row.addWidget(self.mode_badge)
        layout.addLayout(status_row)

        layout.addWidget(self.detail_label)
        layout.addWidget(self.agent_summary)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(6)
        for badge in (
            self.review_mode_badge,
            self.approvals_badge,
            self.risk_badge,
            self.confidence_badge,
        ):
            badge_row.addWidget(badge)
        badge_row.addStretch(1)
        layout.addLayout(badge_row)

        swarm_title = QLabel("Swarm")
        swarm_title.setObjectName("SectionHeaderLabel")
        layout.addWidget(swarm_title)

        swarm_row = QHBoxLayout()
        swarm_row.setSpacing(8)
        swarm_row.addWidget(
            self.start_swarm_dot,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        swarm_row.addWidget(self.start_swarm_label, stretch=1)
        layout.addLayout(swarm_row)

        layout.addWidget(self.start_swarm_detail_label)
        layout.addWidget(self.start_swarm_command_label)

        snapshot_title = QLabel("Snapshot")
        snapshot_title.setObjectName("SectionHeaderLabel")
        layout.addWidget(snapshot_title)
        layout.addWidget(self.overview_body)

        next_step_title = QLabel("Next")
        next_step_title.setObjectName("SectionHeaderLabel")
        layout.addWidget(next_step_title)
        layout.addWidget(self.recommended_step_label)
        layout.addStretch(1)

        return card

    def _build_nav_card(self) -> QFrame:
        """Operator guidance card for the read-first home surface."""
        card = QFrame()
        card.setObjectName("LaneCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title = QLabel("Controls")
        title.setObjectName("LaneAgentName")
        layout.addWidget(title)
        self._nav_intro_label = QLabel(
            "Read here first. Use the toolbar only when you need to act."
        )
        self._nav_intro_label.setObjectName("CardDetailLabel")
        self._nav_intro_label.setWordWrap(True)
        layout.addWidget(self._nav_intro_label)

        self._toolbar_hint_label = QLabel("Toolbar: Refresh, Dry, Live, Roll")
        self._toolbar_hint_label.setObjectName("CardStatusLabel")
        self._toolbar_hint_label.setWordWrap(True)
        layout.addWidget(self._toolbar_hint_label)

        self._page_hint_label = QLabel(
            "Use Workbench or Grid when you want the terminal cards visible together."
        )
        self._page_hint_label.setObjectName("CardDetailLabel")
        self._page_hint_label.setWordWrap(True)
        layout.addWidget(self._page_hint_label)
        layout.addStretch(1)

        return card

    def _build_info_card(self, title: QLabel, body: QLabel) -> QFrame:
        card = QFrame()
        card.setObjectName("LaneCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        layout.addWidget(title)
        layout.addWidget(body, stretch=1)
        return card

    # ── Public API ───────────────────────────────────────────────

    def set_theme_editor_available(self, available: bool) -> None:
        self.theme_button.setEnabled(available)
        if not available:
            self.theme_button.setToolTip(
                "Theme editor is unavailable because PyQt6 theme tooling is not installed."
            )

    def update_state(
        self,
        *,
        audience_mode: str,
        banner: SystemBannerState,
        audience_mode_label: str,
        overview_summary: str,
        overview_body: str,
        repo_summary: str,
        quality_summary: str,
        phone_summary: str,
        next_step: str,
    ) -> None:
        technical_mode = audience_mode == "technical"
        self.set_audience_mode(audience_mode)
        self.health_dot.setProperty("statusLevel", banner.health_level)
        style = self.health_dot.style()
        if style is not None:
            style.unpolish(self.health_dot)
            style.polish(self.health_dot)
        self.health_dot.update()

        self.health_label.setText(banner.health_label)
        self.detail_label.setText(compact_display_text(banner.detail_text, limit=120))
        self.detail_label.setToolTip(banner.detail_text)
        self.agent_summary.setText(
            compact_display_text(banner.agent_summary, limit=150)
        )
        self.agent_summary.setToolTip(banner.agent_summary)
        self.mode_badge.setText(f"Read: {audience_mode_label}")
        self.review_mode_badge.setText(banner.review_mode_text)
        self.approvals_badge.setText(banner.approvals_text)
        self.risk_badge.setText(banner.risk_text)
        self.confidence_badge.setText(banner.confidence_text)
        self.explainer_body.setText(compact_display_text(repo_summary, limit=180))
        overview_display = overview_body if technical_mode else overview_summary
        self.overview_body.setText(compact_display_text(overview_display, limit=220))
        self.next_step_body.setText(compact_display_text(quality_summary, limit=180))
        self.launchpad_body.setText(compact_display_text(phone_summary, limit=180))
        next_display = next_step if technical_mode else f"Next: {next_step}"
        self.recommended_step_label.setText(
            compact_display_text(next_display, limit=120)
        )
        self.overview_body.setToolTip(overview_body)
        self.explainer_body.setToolTip(repo_summary)
        self.next_step_body.setToolTip(quality_summary)
        self.launchpad_body.setToolTip(phone_summary)
        self.recommended_step_label.setToolTip(next_step)

    def set_audience_mode(self, mode: str) -> None:
        """Switch the home workspace between simple and technical presentation."""
        technical_mode = mode == "technical"
        self._primary_title.setText("Ops Snapshot" if technical_mode else "System Health")
        self.explainer_title.setText("Repo Digest" if technical_mode else "Repo")
        self.overview_title.setText("Ops Digest" if technical_mode else "Snapshot")
        self.next_step_title.setText("Quality Digest" if technical_mode else "Quality")
        self.launchpad_title.setText("Relay Digest" if technical_mode else "Relay")
        self._nav_intro_label.setText(
            "Small buttons stay in the chrome. Read the digests here, then act."
            if technical_mode
            else "Read here first. Use the toolbar only when you need to act."
        )
        self._toolbar_hint_label.setText(
            "Toolbar: Refresh | Dry | Live | Roll"
            if technical_mode
            else "Toolbar: Refresh, Dry, Live, Roll"
        )
        self._page_hint_label.setText(
            "Dashboard = lanes. Monitor = raw logs. Reports = digest + staged prompt."
            if technical_mode
            else "Use Workbench or Grid when you want the terminal cards visible together."
        )
        self._apply_digest_mode(technical_mode)

    def set_start_swarm_status(
        self,
        *,
        level: str,
        label: str,
        detail: str,
        command_preview: str | None = None,
    ) -> None:
        """Update the visible Start Swarm health row."""
        apply_swarm_status_widgets(
            dot=self.start_swarm_dot,
            status_label=self.start_swarm_label,
            detail_label=self.start_swarm_detail_label,
            command_label=self.start_swarm_command_label,
            level=level,
            label=label,
            detail=detail,
            command_preview=command_preview,
            detail_tooltip_target=self.start_swarm_button,
        )

    def _make_badge(self, text: str) -> QLabel:
        badge = QLabel(text)
        badge.setObjectName("RoleBadge")
        return badge

    def _apply_digest_mode(self, enabled: bool) -> None:
        for label in self._digest_labels:
            label.setProperty("digestMode", enabled)
            style = label.style()
            if style is not None:
                style.unpolish(label)
                style.polish(label)
            label.update()
