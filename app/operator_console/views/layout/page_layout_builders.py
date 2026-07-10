"""Dedicated layout builders extracted from the shared page mixin."""

from __future__ import annotations

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QSplitter,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover - optional dependency path
    QWidget = object


SIDEBAR_NAV_ITEMS: tuple[tuple[str, str], ...] = (
    ("Home", "home"),
    ("Codex", "codex"),
    ("Codex Session", "codex_session"),
    ("Claude", "claude"),
    ("Claude Session", "claude_session"),
    ("Cursor", "cursor"),
    ("Cursor Session", "cursor_session"),
    ("Operator", "operator"),
    ("Activity", "activity"),
    ("Conversation", "conversation"),
    ("Task Board", "task_board"),
    ("Bridge", "bridge"),
    ("Commands", "commands"),
    ("Diagnostics", "diagnostics"),
)

SIDEBAR_TOOLTIPS: dict[str, str] = {
    "home": "Guided start screen with summary cards and operator guidance.",
    "codex": "Reviewer lane snapshot and detail view.",
    "codex_session": "Reviewer session surface with registry activity and bridge context.",
    "claude": "Implementer lane snapshot and detail view.",
    "claude_session": "Implementer session surface with registry activity and bridge context.",
    "cursor": "Cursor editor lane snapshot and detail view.",
    "cursor_session": "Cursor editor session surface with registry activity and bridge context.",
    "operator": "Human control lane and approval context.",
    "activity": "Plain-language reports, swarm status, and staged AI drafts.",
    "conversation": "Team conversation timeline backed by review-channel packets.",
    "task_board": "Kanban-style task board showing ticket status across agents.",
    "bridge": "Wrapped markdown bridge snapshot.",
    "commands": "Typed launcher command output.",
    "diagnostics": "High-level refresh and command diagnostics.",
}


def build_sidebar_content(window: object) -> QWidget:
    """Build the sidebar navigation layout."""
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setHandleWidth(4)
    splitter.setChildrenCollapsible(False)

    sidebar = QFrame()
    sidebar.setObjectName("SidebarNav")
    sidebar.setMinimumWidth(220)
    sidebar.setMaximumWidth(280)
    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(8, 8, 8, 8)
    sidebar_layout.setSpacing(4)

    window._sidebar_nav = QListWidget()
    window._sidebar_nav.setObjectName("SidebarNavList")
    for label, item_id in SIDEBAR_NAV_ITEMS:
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, item_id)
        item.setToolTip(SIDEBAR_TOOLTIPS.get(item_id, label))
        window._sidebar_nav.addItem(item)

    sidebar_layout.addWidget(window._sidebar_nav, stretch=1)
    sidebar_layout.addWidget(window._approval_container)

    window._sidebar_stack = QStackedWidget()
    window._sidebar_stack.addWidget(window.home_workspace)
    window._sidebar_stack.addWidget(
        window._wrap_in_card(
            window.codex_panel, "Codex", "Reviewer", window._codex_lane_dot
        )
    )
    window._sidebar_stack.addWidget(window._build_session_surface("codex"))
    window._sidebar_stack.addWidget(
        window._wrap_in_card(
            window.claude_panel, "Claude", "Implementer", window._claude_lane_dot
        )
    )
    window._sidebar_stack.addWidget(window._build_session_surface("claude"))
    window._sidebar_stack.addWidget(
        window._wrap_in_card(
            window.cursor_panel, "Cursor", "Editor", window._cursor_lane_dot
        )
    )
    window._sidebar_stack.addWidget(window._build_session_surface("cursor"))
    window._sidebar_stack.addWidget(
        window._wrap_in_card(
            window.operator_panel,
            "Operator",
            "Bridge State",
            window._operator_lane_dot,
        )
    )
    window._sidebar_stack.addWidget(window.activity_workspace)
    window._sidebar_stack.addWidget(window.conversation_panel)
    window._sidebar_stack.addWidget(window.task_board_panel)
    window._sidebar_stack.addWidget(
        window._wrap_in_card(window.raw_bridge_text, "Bridge", "Raw content")
    )
    window._sidebar_stack.addWidget(
        window._wrap_in_card(window.command_output, "Launcher Output", "Command log")
    )
    window._sidebar_stack.addWidget(
        window._wrap_in_card(window.dev_log_text, "Diagnostics", "Event log")
    )

    window._sidebar_nav.currentRowChanged.connect(
        lambda row: window._sidebar_stack.setCurrentIndex(row)
    )
    window._sidebar_nav.setCurrentRow(0)

    splitter.addWidget(sidebar)
    splitter.addWidget(window._sidebar_stack)
    splitter.setStretchFactor(0, 1)
    splitter.setStretchFactor(1, 5)
    splitter.setSizes([240, 1180])
    return splitter


def build_grid_content(window: object) -> QWidget:
    """Build the terminal-first sampler grid."""
    container = QWidget()
    grid = QGridLayout(container)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setSpacing(8)

    codex_card = window._wrap_in_card(
        window.codex_panel, "Codex", "Reviewer", window._codex_lane_dot
    )
    operator_card = window._wrap_in_card(
        window.operator_panel, "Operator", "Bridge State", window._operator_lane_dot
    )
    cursor_card = window._wrap_in_card(
        window.cursor_panel, "Cursor", "Editor", window._cursor_lane_dot
    )
    claude_card = window._wrap_in_card(
        window.claude_panel, "Claude", "Implementer", window._claude_lane_dot
    )
    for card in (codex_card, operator_card, cursor_card, claude_card):
        card.setMaximumHeight(160)

    grid.addWidget(codex_card, 0, 0)
    grid.addWidget(operator_card, 0, 1)
    grid.addWidget(cursor_card, 0, 2)
    grid.addWidget(claude_card, 0, 3)
    grid.addWidget(
        window._wrap_in_card(
            window.command_output,
            "Launcher Output",
            "Dry-run, live, and rollover logs",
        ),
        1,
        0,
        1,
        3,
    )
    grid.addWidget(
        window._wrap_in_card(
            window.dev_log_text,
            "Diagnostics",
            "Desktop shell events",
        ),
        1,
        3,
    )
    grid.addWidget(
        window._wrap_in_card(window.raw_bridge_text, "Bridge", "Raw markdown"),
        2,
        0,
        1,
        3,
    )
    grid.addWidget(window._approval_container, 2, 3)

    grid.setColumnStretch(0, 3)
    grid.setColumnStretch(1, 3)
    grid.setColumnStretch(2, 3)
    grid.setColumnStretch(3, 2)
    grid.setRowStretch(0, 0)
    grid.setRowStretch(1, 5)
    grid.setRowStretch(2, 4)
    return container


def build_analytics_content(window: object) -> QWidget:
    """Build the analytics summary layout."""
    container = QWidget()
    root = QVBoxLayout(container)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(8)

    kpi_row = QHBoxLayout()
    kpi_row.setSpacing(8)
    window._kpi_cards = {}
    for metric_id, label, value in gather_kpi_data():
        card = build_kpi_card(label, value)
        window._kpi_cards[metric_id] = card
        kpi_row.addWidget(card)
    root.addLayout(kpi_row)

    grid = QGridLayout()
    grid.setSpacing(8)
    grid.addWidget(
        window._wrap_in_card(
            window._analytics_text,
            "Snapshot",
            "Live repo and lane health distilled into one readable brief.",
        ),
        0,
        0,
        2,
        2,
    )
    grid.addWidget(
        window._wrap_in_card(
            window._analytics_repo_text,
            "Working Tree",
            "Branch, dirty state, file mix, and hotspot paths.",
        ),
        0,
        2,
    )
    grid.addWidget(
        window._wrap_in_card(
            window._analytics_quality_text,
            "Quality & CI",
            "Warnings, mutation, approvals, and recent pipeline results.",
        ),
        1,
        2,
    )
    grid.addWidget(
        window._wrap_in_card(
            window._analytics_phone_text,
            "Phone Relay",
            "Mobile/control-plane snapshot and current availability.",
        ),
        2,
        0,
    )
    grid.addWidget(window._approval_container, 2, 1, 1, 2)

    grid.setColumnStretch(0, 3)
    grid.setColumnStretch(1, 3)
    grid.setColumnStretch(2, 2)
    grid.setRowStretch(0, 3)
    grid.setRowStretch(1, 3)
    grid.setRowStretch(2, 2)
    root.addLayout(grid, stretch=1)
    return container


def gather_kpi_data() -> list[tuple[str, str, str]]:
    """Return metric tuples for the analytics header strip."""
    return [
        ("dirty_files", "Dirty Files", "—"),
        ("mutation_score", "Mutation", "—"),
        ("ci_runs", "CI Recent", "—"),
        ("warnings", "Warnings", "0"),
        ("pending_approvals", "Pending", "0"),
        ("phone_phase", "Phone", "—"),
    ]


def build_kpi_card(label: str, value: str) -> QFrame:
    """Build a single analytics KPI card."""
    card = QFrame()
    card.setObjectName("KPICard")
    card.setFixedHeight(64)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 6, 14, 6)
    layout.setSpacing(2)

    value_label = QLabel(value)
    value_label.setObjectName("KPIValue")
    layout.addWidget(value_label)

    name_label = QLabel(label)
    name_label.setObjectName("KPILabel")
    layout.addWidget(name_label)
    return card
