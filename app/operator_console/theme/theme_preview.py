"""Live preview gallery for the Operator Console theme editor."""

from __future__ import annotations

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QComboBox,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPlainTextEdit,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False


if _PYQT_AVAILABLE:
    from ..state.models import ApprovalRequest
    from ..views.agent_detail import DiffHighlighter
    from ..views.approval_panel import ApprovalQueuePanel
    from ..views.widgets import KeyValuePanel, ProviderBadge, StatusIndicator

    class ThemePreview(QWidget):
        """Preview gallery built from real Operator Console surfaces."""

        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("ThemePreviewRoot")
            self._diff_highlighter: DiffHighlighter | None = None
            self._diff_view: QPlainTextEdit | None = None

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            layout.addLayout(self._build_preview_row(self._build_toolbar_card(), self._build_home_card()))
            layout.addLayout(self._build_preview_row(self._build_lane_card(), self._build_kpi_card()))
            layout.addLayout(self._build_preview_row(self._build_controls_card(), self._build_tabs_card()))
            layout.addLayout(self._build_preview_row(self._build_approval_card(), self._build_diagnostics_card()))
            layout.addLayout(self._build_preview_row(self._build_diff_card(), self._build_empty_error_card()))
            layout.addStretch(1)
            self.set_preview_theme({})

        def set_preview_theme(self, colors: dict[str, str]) -> None:
            """Refresh preview-only theme wiring that is not driven by QSS alone."""

            if self._diff_view is None:
                return
            self._diff_highlighter = DiffHighlighter(self._diff_view.document(), colors)

        def _build_preview_row(self, left: QWidget, right: QWidget) -> QHBoxLayout:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(10)
            row.addWidget(left, 1)
            row.addWidget(right, 1)
            return row

        def _build_toolbar_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("LaneCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)

            title = QLabel("Toolbar + Header")
            title.setObjectName("LaneAgentName")
            detail = QLabel("Top chrome, provider badges, settings labels, and quick actions")
            detail.setObjectName("CardDetailLabel")
            detail.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(detail)

            toolbar = QFrame()
            toolbar.setObjectName("Toolbar")
            toolbar_layout = QHBoxLayout(toolbar)
            toolbar_layout.setContentsMargins(10, 8, 10, 8)
            toolbar_layout.setSpacing(8)

            toolbar_title = QLabel("Operator Console")
            toolbar_title.setObjectName("ToolbarTitle")
            toolbar_layout.addWidget(toolbar_title)

            for provider_name, level in (("Codex", "active"), ("Claude", "warning")):
                dot = StatusIndicator()
                dot.set_level(level)
                toolbar_layout.addWidget(dot)
                badge = ProviderBadge(provider_name)
                toolbar_layout.addWidget(badge)
                agent_label = QLabel(provider_name)
                agent_label.setObjectName("ToolbarAgentLabel")
                toolbar_layout.addWidget(agent_label)

            toolbar_layout.addStretch(1)

            settings_label = QLabel("Theme")
            settings_label.setObjectName("ToolbarSettingLabel")
            toolbar_layout.addWidget(settings_label)

            workbench_btn = QPushButton("Workbench")
            workbench_btn.setObjectName("SmallActionButton")
            toolbar_layout.addWidget(workbench_btn)

            layout.addWidget(toolbar)
            return card

        def _build_home_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("LaneCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)

            title = QLabel("Home / Launchpad")
            title.setObjectName("LaneAgentName")
            subtitle = QLabel("Guided start surface, badges, and action rows")
            subtitle.setObjectName("CardDetailLabel")
            subtitle.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(subtitle)

            badges = QHBoxLayout()
            badges.setSpacing(8)
            for text in ("Read: Simple", "Mode: review", "Approvals: 1"):
                badge = QLabel(text)
                badge.setObjectName("RoleBadge")
                badges.addWidget(badge)
            badges.addStretch(1)
            layout.addLayout(badges)

            body = QLabel(
                "Use the Home screen when you want the app to explain the current "
                "state before dropping into raw monitors."
            )
            body.setObjectName("CardStatusLabel")
            body.setWordWrap(True)
            layout.addWidget(body)
            return card

        def _build_kpi_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("KPICard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(4)

            value = QLabel("97%")
            value.setObjectName("KPIValue")
            label = QLabel("Launch Health")
            label.setObjectName("KPILabel")

            layout.addWidget(value)
            layout.addWidget(label)
            return card

        def _build_lane_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("LaneCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            header = QHBoxLayout()
            header.setSpacing(8)
            dot = StatusIndicator()
            dot.set_level("active")
            header.addWidget(dot)

            title_col = QVBoxLayout()
            title_col.setSpacing(2)
            name = QLabel("Codex Lane")
            name.setObjectName("LaneAgentName")
            role = QLabel("Reviewer / Operator Preview")
            role.setObjectName("LaneRoleLabel")
            title_col.addWidget(name)
            title_col.addWidget(role)
            header.addLayout(title_col, 1)

            badge = QLabel("ACTIVE")
            badge.setObjectName("RoleBadge")
            header.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)
            layout.addLayout(header)

            panel = KeyValuePanel("Bridge Snapshot")
            panel.set_status("active")
            panel.set_rows(
                [
                    ("status", "healthy"),
                    ("theme", "live preview"),
                    ("layout", "tabbed / left workbench"),
                ]
            )
            panel.set_raw_text(
                "provider: codex\n"
                "status: healthy\n"
                "theme: live preview\n"
                "layout: tabbed / left workbench\n"
            )
            layout.addWidget(panel)
            return card

        def _build_tabs_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("AgentSummaryCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)

            title = QLabel("Tabs + Navigation")
            title.setObjectName("CardAgentName")
            subtitle = QLabel("Sidebar tabs, monitor tabs, and selected state chrome")
            subtitle.setObjectName("CardLaneLabel")
            subtitle.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(subtitle)

            nav_tabs = QTabWidget()
            nav_tabs.setObjectName("NavTabs")
            nav_tabs.tabBar().setObjectName("NavTabBar")
            nav_tabs.addTab(QLabel("Launchpad summary"), "Home")
            nav_tabs.addTab(QLabel("Lane cards"), "Lanes")
            nav_tabs.addTab(QLabel("CI and reports"), "Reports")
            nav_tabs.setCurrentIndex(1)
            layout.addWidget(nav_tabs)

            monitor_tabs = QTabWidget()
            monitor_tabs.setObjectName("MonitorTabs")
            monitor_tabs.tabBar().setObjectName("MonitorTabBar")
            monitor_tabs.addTab(QLabel("Codex bridge output"), "Codex")
            monitor_tabs.addTab(QLabel("Claude bridge output"), "Claude")
            monitor_tabs.setCurrentIndex(0)
            layout.addWidget(monitor_tabs)
            return card

        def _build_controls_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("AgentSummaryCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)

            title = QLabel("Controls")
            title.setObjectName("CardAgentName")
            subtitle = QLabel("Buttons, inputs, sidebar, and list surfaces")
            subtitle.setObjectName("CardLaneLabel")
            layout.addWidget(title)
            layout.addWidget(subtitle)

            controls = QHBoxLayout()
            controls.setSpacing(8)

            left = QVBoxLayout()
            left.setSpacing(8)
            line = QLineEdit()
            line.setPlaceholderText("Search the review state")
            combo = QComboBox()
            combo.addItems(["Codex", "Claude", "Operator"])
            buttons = QHBoxLayout()
            primary = QPushButton("Launch")
            primary.setProperty("accentRole", "primary")
            warning = QPushButton("Rollover")
            warning.setProperty("accentRole", "warning")
            neutral = QPushButton("Notes")
            buttons.addWidget(primary)
            buttons.addWidget(warning)
            buttons.addWidget(neutral)
            left.addWidget(line)
            left.addWidget(combo)
            left.addLayout(buttons)

            sidebar = QListWidget()
            sidebar.setObjectName("SidebarNavList")
            for label in ("Overview", "Bridge", "Approvals", "Diagnostics"):
                sidebar.addItem(QListWidgetItem(label))
            sidebar.setCurrentRow(1)

            controls.addLayout(left, 2)
            controls.addWidget(sidebar, 1)
            layout.addLayout(controls)
            return card

        def _build_approval_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("LaneCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)

            title = QLabel("Approval Queue")
            title.setObjectName("LaneAgentName")
            detail = QLabel("Severity chips, detail pane, and decision buttons")
            detail.setObjectName("CardDetailLabel")
            detail.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(detail)

            panel = ApprovalQueuePanel()
            panel.set_approvals(
                (
                    ApprovalRequest(
                        packet_id="pkt-204",
                        from_agent="codex",
                        to_agent="operator",
                        summary="Approve guarded launch with live bridge handoff",
                        body="Dry run is green. Live launch will reuse the current repo-visible artifacts.",
                        policy_hint="human_review_required/high-risk",
                        requested_action="launch_live",
                        status="pending",
                        evidence_refs=("dev/active/review_channel.md",),
                    ),
                )
            )
            panel.setMaximumHeight(250)
            layout.addWidget(panel)
            return card

        def _build_diagnostics_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("LaneCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)

            title = QLabel("Diagnostics + Logs")
            title.setObjectName("LaneAgentName")
            detail = QLabel("Repo-visible monitors, logs, and compact state callouts")
            detail.setObjectName("CardDetailLabel")
            detail.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(detail)

            raw = QPlainTextEdit()
            raw.setObjectName("PanelRawText")
            raw.setReadOnly(True)
            raw.setMaximumHeight(170)
            raw.setPlainText(
                "[info] review_channel.launch dry-run ok\n"
                "[info] active_plan_sync ok\n"
                "[warn] workflow history not wired in this preview\n"
                "[next] run live launch from Home when operator is ready\n"
            )
            layout.addWidget(raw)

            hint = QLabel("Preview-only diagnostics stay honest about what is not wired yet.")
            hint.setObjectName("CardStatusLabel")
            hint.setWordWrap(True)
            layout.addWidget(hint)
            return card

        def _build_diff_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("AgentSummaryCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)

            title = QLabel("Diff / Raw Text")
            title.setObjectName("CardAgentName")
            detail = QLabel("Monospace, borders, padding, and diff colors")
            detail.setObjectName("CardDetailLabel")
            layout.addWidget(title)
            layout.addWidget(detail)

            self._diff_view = QPlainTextEdit()
            self._diff_view.setObjectName("DiffView")
            self._diff_view.setReadOnly(True)
            self._diff_view.setPlainText(
                "diff --git a/theme.py b/theme.py\n"
                "--- a/theme.py\n"
                "+++ b/theme.py\n"
                "@@\n"
                "+ accent = \"#5cb8ff\"\n"
                "- accent = \"#4fa0e8\"\n"
            )
            self._diff_view.setMaximumHeight(150)
            layout.addWidget(self._diff_view)
            return card

        def _build_empty_error_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("LaneCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)

            title = QLabel("Empty + Error States")
            title.setObjectName("LaneAgentName")
            subtitle = QLabel("Representative muted, warning, and stale status surfaces")
            subtitle.setObjectName("CardDetailLabel")
            subtitle.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(subtitle)

            empty_row = QHBoxLayout()
            empty_row.setSpacing(8)
            empty_dot = StatusIndicator()
            empty_dot.set_level("idle")
            empty_row.addWidget(empty_dot)
            empty_label = QLabel("No pending approvals yet")
            empty_label.setObjectName("CardStatusLabel")
            empty_row.addWidget(empty_label)
            empty_row.addStretch(1)
            layout.addLayout(empty_row)

            warning_row = QHBoxLayout()
            warning_row.setSpacing(8)
            warning_dot = StatusIndicator()
            warning_dot.set_level("warning")
            warning_row.addWidget(warning_dot)
            warning_label = QLabel("Workflow history still depends on repo-visible reports")
            warning_label.setObjectName("CardStatusLabel")
            warning_label.setWordWrap(True)
            warning_row.addWidget(warning_label, 1)
            layout.addLayout(warning_row)

            stale_row = QHBoxLayout()
            stale_row.setSpacing(8)
            stale_dot = StatusIndicator()
            stale_dot.set_level("stale")
            stale_row.addWidget(stale_dot)
            stale_badge = QLabel("NOT WIRED")
            stale_badge.setObjectName("RoleBadge")
            stale_row.addWidget(stale_badge)
            stale_hint = QLabel("Preview keeps honest placeholders visible instead of implying live data.")
            stale_hint.setObjectName("CardDetailLabel")
            stale_hint.setWordWrap(True)
            stale_row.addWidget(stale_hint, 1)
            layout.addLayout(stale_row)
            layout.addStretch(1)
            return card

else:

    class ThemePreview:  # type: ignore[no-redef]
        """Stub when PyQt6 is not installed."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass
