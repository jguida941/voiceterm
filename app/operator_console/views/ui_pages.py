"""Page builders and layout modes for the Operator Console.

Provides mixin methods that OperatorConsoleWindow inherits to construct
different spatial arrangements of the same data widgets:

  Tabbed    — Dashboard / Monitor / Activity tabs (default)
  Sidebar   — Codex-style nav list + content panel
  Grid      — Sampler-style tiled dashboard
  Analytics — Repo-visible review-signal dashboard
"""

from __future__ import annotations

from .layout.page_layout_builders import (
    SIDEBAR_NAV_ITEMS,
    build_analytics_content,
    build_grid_content,
    build_kpi_card,
    build_sidebar_content,
    gather_kpi_data,
)
from .layout.ui_layouts import resolve_layout
from .layout.workbench_layout import build_workbench_content
from .shared.widgets import FlippableTextCard, ProviderBadge, StatusIndicator

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QSplitter,
        QStackedWidget,
        QTabWidget,
        QVBoxLayout,
        QPushButton,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False


class PageBuilderMixin:
    """Layout methods mixed into OperatorConsoleWindow."""

    # Maps panel widget → (name_label, role_label) in the card header
    # so refresh_snapshot can update roles dynamically from lane data.
    _lane_card_labels: dict

    # ── Layout switching ─────────────────────────────────────

    def _reset_layout_handles(self) -> None:
        """Drop references to layout-owned widgets before rebuilding."""
        self._nav_tabs = None
        self._monitor_tabs = None
        self._workbench_tabs = None
        self._sidebar_nav = None
        self._sidebar_stack = None
        self._kpi_cards = {}
        self._monitor_surface_indexes = {}
        self._workbench_surface_indexes = {}
        self._workbench_root_splitter = None
        self._workbench_lane_splitter = None
        self._workbench_utility_splitter = None
        self._workbench_preset_buttons = {}
        self._workbench_preset_label = None
        self.codex_session_detail_card = None
        self.claude_session_detail_card = None
        self.cursor_session_detail_card = None

    def _reveal_output_surface(self, surface_id: str) -> None:
        """Make a monitor surface visible in the current layout when possible."""
        if surface_id == "command_output":
            if self._layout_mode == "tabbed":
                if self._nav_tabs is not None and self._monitor_tabs is not None:
                    self._nav_tabs.setCurrentIndex(2)
                    self._select_monitor_surface("command_output")
                return
            if self._layout_mode == "workbench" and self._monitor_tabs is not None:
                self._select_workbench_surface("terminal")
                self._select_monitor_surface("command_output")
                return
            if self._layout_mode == "sidebar" and self._sidebar_nav is not None:
                for row, (_label, item_id) in enumerate(SIDEBAR_NAV_ITEMS):
                    if item_id == "commands":
                        self._sidebar_nav.setCurrentRow(row)
                        break
                return

        if surface_id == "diagnostics":
            if self._layout_mode == "tabbed":
                if self._nav_tabs is not None and self._monitor_tabs is not None:
                    self._nav_tabs.setCurrentIndex(2)
                    self._select_monitor_surface("diagnostics")
                return
            if self._layout_mode == "workbench" and self._monitor_tabs is not None:
                self._select_workbench_surface("terminal")
                self._select_monitor_surface("diagnostics")
                return
            if self._layout_mode == "sidebar" and self._sidebar_nav is not None:
                for row, (_label, item_id) in enumerate(SIDEBAR_NAV_ITEMS):
                    if item_id == "diagnostics":
                        self._sidebar_nav.setCurrentRow(row)
                        break

    def _select_monitor_surface(self, surface_id: str) -> None:
        """Select a monitor tab by logical surface id."""
        if self._monitor_tabs is None:
            return
        index = getattr(self, "_monitor_surface_indexes", {}).get(surface_id)
        if index is not None:
            self._monitor_tabs.setCurrentIndex(index)

    def _select_workbench_surface(self, surface_id: str) -> None:
        """Select a workbench page tab by logical surface id."""
        if self._workbench_tabs is None:
            return
        index = getattr(self, "_workbench_surface_indexes", {}).get(surface_id)
        if index is not None:
            self._workbench_tabs.setCurrentIndex(index)

    def _navigate_primary_surface(self, surface_id: str) -> None:
        """Navigate to a top-level surface across tabbed and sidebar modes."""
        if self._layout_mode == "tabbed" and self._nav_tabs is not None:
            tab_indexes = {
                "home": 0,
                "dashboard": 1,
                "monitor": 2,
                "activity": 3,
                "collaborate": 4,
            }
            index = tab_indexes.get(surface_id)
            if index is not None:
                self._nav_tabs.setCurrentIndex(index)
            return
        if self._layout_mode == "workbench":
            workbench_targets = {
                "home": "sessions",
                "dashboard": "stats",
                "monitor": "terminal",
                "activity": "reports",
            }
            target = workbench_targets.get(surface_id)
            if target is not None:
                self._select_workbench_surface(target)
            return
        if self._layout_mode == "sidebar" and self._sidebar_nav is not None:
            for row, (_label, item_id) in enumerate(SIDEBAR_NAV_ITEMS):
                if item_id == surface_id:
                    self._sidebar_nav.setCurrentRow(row)
                    return

    def _persistent_widgets(self) -> list[QWidget]:
        """All data widgets that survive layout switches."""
        return [
            self.home_workspace,
            self.codex_panel,
            self.claude_panel,
            self.operator_panel,
            self.cursor_panel,
            self.codex_session_text,
            self.codex_session_stats_text,
            self.codex_session_registry_text,
            self.claude_session_text,
            self.claude_session_stats_text,
            self.claude_session_registry_text,
            self.cursor_session_text,
            self.cursor_session_stats_text,
            self.cursor_session_registry_text,
            self.raw_bridge_text,
            self.timeline_panel,
            self.command_output,
            self.dev_log_text,
            self.activity_workspace,
            self.workbench_codex_card,
            self.workbench_operator_card,
            self.workbench_claude_card,
            self.workbench_cursor_card,
            self._analytics_text,
            self._analytics_repo_text,
            self._analytics_quality_text,
            self._analytics_phone_text,
            self._codex_lane_dot,
            self._claude_lane_dot,
            self._cursor_lane_dot,
            self._operator_lane_dot,
            self._approval_container,
            self.workflow_header_bar,
            self.workflow_timeline_footer,
            self.conversation_panel,
            self.task_board_panel,
        ]

    def _build_content_for_mode(self, mode_id: str) -> QWidget:
        """Build the content widget for a given layout mode.

        Resets layout-owned references so refresh_snapshot only touches
        live widgets after a mode change.  After the layout builder
        returns, any persistent widgets that were not placed in the new
        layout are stashed in a hidden holder so they remain parented
        (preventing top-level window flicker) without coupling individual
        layout builders to widgets they do not use.
        """
        self._reset_layout_handles()
        self._lane_card_labels = {}
        if mode_id == "sidebar":
            content = build_sidebar_content(self)
        elif mode_id == "grid":
            content = build_grid_content(self)
        elif mode_id == "analytics":
            content = build_analytics_content(self)
        elif mode_id == "workbench":
            content = build_workbench_content(self)
        else:
            content = self._build_tabbed_content()
        self._stash_unplaced_widgets(content)
        return content

    def _stash_unplaced_widgets(self, content: QWidget) -> None:
        """Parent any persistent widgets not placed by the current layout.

        This eliminates the need for individual layout builders to create
        hidden holder hacks for widgets they do not display.
        """
        unplaced = [w for w in self._persistent_widgets() if w.parent() is None]
        if not unplaced:
            return
        holder = getattr(self, "_offscreen_holder", None)
        if holder is None:
            holder = QStackedWidget(content)
            holder.setVisible(False)
            self._offscreen_holder = holder
        else:
            holder.setParent(content)
        for widget in unplaced:
            holder.addWidget(widget)

    def _switch_layout(self, mode_id: str) -> None:
        """Swap the content area to a different layout mode."""
        # Detach all persistent widgets so the old container can be
        # deleted without destroying them
        for widget in self._persistent_widgets():
            widget.setParent(None)

        old = self._content_widget
        self._root_layout.removeWidget(old)
        old.deleteLater()

        new = self._build_content_for_mode(mode_id)
        self._root_layout.addWidget(new, stretch=1)
        self._content_widget = new
        self._layout_mode = mode_id

    # ── Toolbar ──────────────────────────────────────────────

    def _build_toolbar(self) -> QFrame:
        """Thin toolbar: title + status dots + actions + settings."""
        bar = QFrame()
        bar.setObjectName("Toolbar")
        bar.setFixedHeight(36)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)

        title = QLabel("VoiceTerm")
        title.setObjectName("ToolbarTitle")
        layout.addWidget(title)

        for dot, name in [
            (self.codex_dot, "Codex"),
            (self.claude_dot, "Claude"),
            (self.cursor_dot, "Cursor"),
            (self.operator_dot, "Operator"),
        ]:
            layout.addWidget(ProviderBadge(name))
            layout.addWidget(dot)
            dot.setToolTip(f"{name} lane status")

        layout.addStretch(1)

        for btn in [
            self.refresh_button,
            self.launch_dry_button,
            self.launch_live_button,
            self.rollover_button,
        ]:
            layout.addWidget(btn)

        return bar

    # ── Shared helpers ───────────────────────────────────────

    def _wrap_in_card(
        self,
        widget: QWidget,
        title: str,
        subtitle: str,
        dot: StatusIndicator | None = None,
    ) -> QFrame:
        """Wrap a data widget in a themed card frame with a header.

        When the widget has its own SectionHeader (like KeyValuePanel),
        that header is hidden to avoid duplicate titles and dots.
        The card header becomes the single identity source, and its
        role label is registered for dynamic updates during refresh.
        """
        card = QFrame()
        card.setObjectName("LaneCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        if dot is not None:
            header.addWidget(dot)
            dot.setToolTip(f"{title} lane status")
        header.addWidget(ProviderBadge(title))
        name_label = QLabel(title)
        name_label.setObjectName("LaneAgentName")
        header.addWidget(name_label)
        role_label = QLabel(f"— {subtitle}")
        role_label.setObjectName("LaneRoleLabel")
        header.addWidget(role_label)
        header.addStretch(1)

        # Detail button for agent lane panels
        agent_id = self._detect_agent_id(widget)
        if agent_id is not None:
            detail_btn = QPushButton("\u22ef")
            detail_btn.setObjectName("CardDetailButton")
            detail_btn.setFixedSize(28, 28)
            detail_btn.setToolTip(f"View {title} details")
            detail_btn.clicked.connect(
                lambda checked, aid=agent_id: self._show_agent_detail(aid)
            )
            header.addWidget(detail_btn)

        layout.addLayout(header)

        # Hide the panel's own SectionHeader to avoid duplicate title + dot
        if hasattr(widget, "header"):
            widget.header.setVisible(False)

        # Register for dynamic role updates from lane data
        if not hasattr(self, "_lane_card_labels"):
            self._lane_card_labels = {}
        self._lane_card_labels[id(widget)] = (name_label, role_label)

        layout.addWidget(widget, stretch=1)
        return card

    def _detect_agent_id(self, widget: QWidget) -> str | None:
        """Map a panel widget to its agent identifier for detail dialogs."""
        if widget is getattr(self, "codex_panel", None):
            return "codex"
        if widget is getattr(self, "claude_panel", None):
            return "claude"
        if widget is getattr(self, "cursor_panel", None):
            return "cursor"
        if widget is getattr(self, "operator_panel", None):
            return "operator"
        return None

    def _wrap_support_card(
        self,
        widget: QWidget,
        title: str,
        subtitle: str,
        *,
        provider_name: str | None = None,
    ) -> QFrame:
        """Wrap a support widget in a lane-styled card without dynamic lane wiring."""
        card = QFrame()
        card.setObjectName("LaneCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        if provider_name:
            header.addWidget(ProviderBadge(provider_name))
        name_label = QLabel(title)
        name_label.setObjectName("LaneAgentName")
        header.addWidget(name_label)
        role_label = QLabel(f"— {subtitle}")
        role_label.setObjectName("LaneRoleLabel")
        header.addWidget(role_label)
        header.addStretch(1)
        layout.addLayout(header)
        layout.addWidget(widget, stretch=1)
        return card

    def _build_session_surface(self, provider_id: str) -> QWidget:
        """Compose terminal history plus a flippable stats/registry card."""
        provider_label = provider_id.capitalize()
        terminal_widget = getattr(self, f"{provider_id}_session_text")
        stats_widget = getattr(self, f"{provider_id}_session_stats_text")
        registry_widget = getattr(self, f"{provider_id}_session_registry_text")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        split = QSplitter(Qt.Orientation.Vertical)
        split.setHandleWidth(4)
        split.setChildrenCollapsible(False)
        split.addWidget(
            self._wrap_support_card(
                terminal_widget,
                f"{provider_label} Terminal",
                "Recent history",
                provider_name=provider_label,
            )
        )
        detail_card = FlippableTextCard(
            front_widget=stats_widget,
            back_widget=registry_widget,
            front_title=f"{provider_label} Stats",
            front_subtitle="Freshness, signals, and screen",
            back_title=f"{provider_label} Registry",
            back_subtitle="Lane assignments and states",
            provider_name=provider_label,
        )
        setattr(self, f"{provider_id}_session_detail_card", detail_card)

        split.addWidget(detail_card)
        split.setStretchFactor(0, 7)
        split.setStretchFactor(1, 4)
        layout.addWidget(split, stretch=1)
        return container

    # ═══════════════════════════════════════════════════════════
    # TABBED LAYOUT — Dashboard | Monitor | Activity
    # ═══════════════════════════════════════════════════════════

    def _build_tabbed_content(self) -> QWidget:
        """Top-level tabbed navigation: Dashboard | Monitor | Activity."""
        self._nav_tabs = QTabWidget()
        self._nav_tabs.setObjectName("NavTabs")
        self._nav_tabs.setDocumentMode(True)
        self._nav_tabs.tabBar().setObjectName("NavTabBar")
        self._nav_tabs.tabBar().setExpanding(False)

        self._nav_tabs.addTab(self._build_home_page(), "Home")
        self._nav_tabs.addTab(self._build_dashboard_page(), "Dashboard")
        self._nav_tabs.addTab(self._build_monitor_page(), "Monitor")
        self._nav_tabs.addTab(self._build_activity_page(), "Activity")
        self._nav_tabs.addTab(self._build_collaborate_page(), "Collaborate")
        self._nav_tabs.tabBar().setTabToolTip(
            0, "Guided home screen with simple or technical overview."
        )
        self._nav_tabs.tabBar().setTabToolTip(
            1, "Primary lane dashboard for Codex, Operator, Cursor, and Claude."
        )
        self._nav_tabs.tabBar().setTabToolTip(
            2, "Codex, Cursor, and Claude session surfaces plus bridge, launcher output, and diagnostics."
        )
        self._nav_tabs.tabBar().setTabToolTip(
            3, "Plain-language reports, quick actions, and staged AI drafts."
        )
        self._nav_tabs.tabBar().setTabToolTip(
            4, "Team conversation and task board backed by review-channel packets."
        )

        return self._nav_tabs

    def _build_home_page(self) -> QWidget:
        """Guided home/start surface."""
        return self.home_workspace

    def _build_dashboard_page(self) -> QWidget:
        """Readable live-lane overview with approvals anchored below."""
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)

        codex_card = self._wrap_in_card(
            self.codex_panel, "Codex", "Reviewer", self._codex_lane_dot
        )
        operator_card = self._wrap_in_card(
            self.operator_panel, "Operator", "Bridge State", self._operator_lane_dot
        )
        cursor_card = self._wrap_in_card(
            self.cursor_panel, "Cursor", "Editor", self._cursor_lane_dot
        )
        claude_card = self._wrap_in_card(
            self.claude_panel, "Claude", "Implementer", self._claude_lane_dot
        )
        for card in (codex_card, operator_card, cursor_card, claude_card):
            card.setMaximumHeight(216)

        grid.addWidget(codex_card, 0, 0)
        grid.addWidget(operator_card, 0, 1)
        grid.addWidget(cursor_card, 0, 2)
        grid.addWidget(claude_card, 0, 3)
        grid.addWidget(self._approval_container, 1, 0, 1, 4)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 1)
        return container

    def _build_monitor_page(self) -> QWidget:
        """Operational logs plus per-agent session surfaces."""
        self._monitor_tabs = QTabWidget()
        self._monitor_tabs.setObjectName("MonitorTabs")
        self._monitor_tabs.setDocumentMode(True)
        self._monitor_tabs.tabBar().setObjectName("MonitorTabBar")
        self._monitor_tabs.tabBar().setExpanding(True)
        monitor_panels = (
            ("codex_session", self._build_session_surface("codex"), "Codex Session"),
            ("claude_session", self._build_session_surface("claude"), "Claude Session"),
            ("cursor_session", self._build_session_surface("cursor"), "Cursor Session"),
            ("bridge", self.raw_bridge_text, "Bridge"),
            ("command_output", self.command_output, "Launcher Output"),
            ("diagnostics", self.dev_log_text, "Diagnostics"),
        )
        self._monitor_surface_indexes = {}
        for surface_id, widget, label in monitor_panels:
            index = self._monitor_tabs.addTab(widget, label)
            self._monitor_surface_indexes[surface_id] = index
        self._monitor_tabs.tabBar().setTabToolTip(
            self._monitor_surface_indexes["codex_session"],
            "Reviewer session surface: registry activity plus the current bridge summary.",
        )
        self._monitor_tabs.tabBar().setTabToolTip(
            self._monitor_surface_indexes["claude_session"],
            "Implementer session surface: registry activity plus the current bridge summary.",
        )
        self._monitor_tabs.tabBar().setTabToolTip(
            self._monitor_surface_indexes["cursor_session"],
            "Cursor editor session surface: live terminal traces and registry assignments.",
        )
        self._monitor_tabs.tabBar().setTabToolTip(
            self._monitor_surface_indexes["bridge"],
            "Wrapped markdown bridge snapshot from repo-visible state.",
        )
        self._monitor_tabs.tabBar().setTabToolTip(
            self._monitor_surface_indexes["command_output"],
            "Output from typed launch, dry-run, and rollover commands.",
        )
        self._monitor_tabs.tabBar().setTabToolTip(
            self._monitor_surface_indexes["diagnostics"],
            "High-level app events, warnings, and diagnostics.",
        )
        return self._monitor_tabs

    def _build_activity_page(self) -> QWidget:
        """Agent connections: what each lane is working on."""
        return self.activity_workspace

    def _build_collaborate_page(self) -> QWidget:
        """Team conversation and task board in a vertical split."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(4)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.conversation_panel)
        splitter.addWidget(self.task_board_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, stretch=1)
        return container

    def _build_center_spine(self, *, include_approvals: bool = True) -> QFrame:
        """Center column for operator state, optionally with approvals."""
        spine = QFrame()
        spine.setObjectName("LaneCard")
        layout = QVBoxLayout(spine)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(self._operator_lane_dot)
        self._operator_lane_dot.setToolTip("Operator lane status")
        header.addWidget(ProviderBadge("Operator"))
        name_label = QLabel("Operator")
        name_label.setObjectName("LaneAgentName")
        header.addWidget(name_label)
        role_label = QLabel("— Operator Bridge State")
        role_label.setObjectName("LaneRoleLabel")
        header.addWidget(role_label)
        header.addStretch(1)

        detail_btn = QPushButton("\u22ef")
        detail_btn.setObjectName("CardDetailButton")
        detail_btn.setFixedSize(28, 28)
        detail_btn.setToolTip("View Operator details")
        detail_btn.clicked.connect(
            lambda checked: self._show_agent_detail("operator")
        )
        header.addWidget(detail_btn)
        layout.addLayout(header)

        # Register for dynamic role updates from lane data
        if not hasattr(self, "_lane_card_labels"):
            self._lane_card_labels = {}
        self._lane_card_labels[id(self.operator_panel)] = (name_label, role_label)

        # Hide duplicate panel header
        if hasattr(self.operator_panel, "header"):
            self.operator_panel.header.setVisible(False)

        if include_approvals:
            center_split = QSplitter(Qt.Orientation.Vertical)
            center_split.setHandleWidth(3)
            center_split.setChildrenCollapsible(False)
            center_split.addWidget(self.operator_panel)
            center_split.addWidget(self._approval_container)
            center_split.setStretchFactor(0, 2)
            center_split.setStretchFactor(1, 3)
            layout.addWidget(center_split, stretch=1)
        else:
            layout.addWidget(self.operator_panel, stretch=1)

        return spine

    # ═══════════════════════════════════════════════════════════
    # SIDEBAR LAYOUT — Codex-style nav + content panel
    # ═══════════════════════════════════════════════════════════

    # Callers use build_sidebar_content(self) directly from
    # .layout.page_layout_builders — no mixin wrapper needed.

    # ═══════════════════════════════════════════════════════════
    # GRID LAYOUT — Sampler-style tiled dashboard
    # ═══════════════════════════════════════════════════════════

    # Callers use build_grid_content(self) directly from
    # .layout.page_layout_builders — no mixin wrapper needed.

    # ═══════════════════════════════════════════════════════════
    # ANALYTICS LAYOUT — repo-visible bridge and lane signals
    # ═══════════════════════════════════════════════════════════

    # Callers use build_analytics_content(self), gather_kpi_data(),
    # and build_kpi_card() directly from .layout.page_layout_builders
    # — no mixin wrappers needed.
