"""Workbench layout helpers for the Operator Console.

The workbench is organized by job: full-page tabs for sessions, live terminal
streams, status boards, approvals, and reports.
"""

from __future__ import annotations

from .ui_layouts import resolve_workbench_preset

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QGridLayout,
        QSplitter,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object


def build_workbench_content(window: object) -> QWidget:
    """Build the workbench as task-oriented full-page tabs."""
    workbench_tabs, session_splitter, terminal_splitter = _build_workbench_tabs(window)

    window._workbench_root_splitter = None  # type: ignore[attr-defined]
    window._workbench_lane_splitter = session_splitter  # type: ignore[attr-defined]
    window._workbench_utility_splitter = terminal_splitter  # type: ignore[attr-defined]
    window._workbench_tabs = workbench_tabs  # type: ignore[attr-defined]
    window._workbench_preset_buttons = {}  # type: ignore[attr-defined]
    window._workbench_preset_label = None  # type: ignore[attr-defined]

    apply_workbench_preset(
        window,
        getattr(window, "_workbench_preset", "balanced"),
        announce=False,
    )
    return workbench_tabs


def apply_workbench_preset(
    window: object,
    preset_id: str,
    *,
    announce: bool,
) -> None:
    """Apply internal workbench ratios without exposing a preset rail."""
    preset = resolve_workbench_preset(preset_id)
    root_splitter = getattr(window, "_workbench_root_splitter", None)
    lane_splitter = getattr(window, "_workbench_lane_splitter", None)
    center_splitter = getattr(window, "_workbench_utility_splitter", None)
    if lane_splitter is None and center_splitter is None:
        return

    if root_splitter is not None:
        _set_splitter_sizes(root_splitter, preset.root_sizes)
    if lane_splitter is not None:
        _set_splitter_sizes(lane_splitter, preset.lane_sizes)
    if center_splitter is not None:
        _set_splitter_sizes(center_splitter, preset.utility_sizes)
    window._workbench_preset = preset.preset_id  # type: ignore[attr-defined]

    if announce:
        window._record_event(  # type: ignore[attr-defined]
            "INFO",
            "workbench_preset_changed",
            "Operator Console workbench preset changed",
            details={"preset_id": preset.preset_id},
        )
        window.statusBar().showMessage(  # type: ignore[attr-defined]
            f"Workbench preset: {preset.display_name}"
        )


def _build_session_page(window: object) -> QSplitter:
    """Render the session-focused page with all three live lanes visible."""
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setHandleWidth(4)
    splitter.setChildrenCollapsible(False)
    splitter.addWidget(
        window._wrap_in_card(  # type: ignore[attr-defined]
            window.codex_session_text,
            "Codex Session",
            "Registry + bridge",
        )
    )
    splitter.addWidget(window._build_center_spine(include_approvals=False))  # type: ignore[attr-defined]
    splitter.addWidget(
        window._wrap_in_card(  # type: ignore[attr-defined]
            window.claude_session_text,
            "Claude Session",
            "Registry + bridge",
        )
    )
    splitter.setStretchFactor(0, 5)
    splitter.setStretchFactor(1, 2)
    splitter.setStretchFactor(2, 5)
    return splitter


def _build_terminal_page(window: object) -> QSplitter:
    """Render the terminal-focused page with streams and high-signal status."""
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setHandleWidth(4)
    splitter.setChildrenCollapsible(False)
    splitter.addWidget(_build_log_monitor_tabs(window))
    splitter.addWidget(
        window._wrap_in_card(  # type: ignore[attr-defined]
            window._analytics_text,
            "Snapshot",
            "Repo and lane health at a glance.",
        )
    )
    splitter.addWidget(
        window._wrap_in_card(  # type: ignore[attr-defined]
            window._analytics_quality_text,
            "Quality",
            "Warnings, approvals, mutation, and CI signals.",
        )
    )
    splitter.setStretchFactor(0, 7)
    splitter.setStretchFactor(1, 3)
    splitter.setStretchFactor(2, 2)
    return splitter


def _build_workbench_tabs(window: object) -> tuple[QTabWidget, QSplitter, QSplitter]:
    """Group the workbench into full-page tabs by operator job."""
    tabs = QTabWidget()
    tabs.setObjectName("MonitorTabs")
    tabs.setDocumentMode(True)
    tabs.tabBar().setObjectName("MonitorTabBar")
    tabs.tabBar().setExpanding(True)

    session_page = _build_session_page(window)
    terminal_page = _build_terminal_page(window)
    stats_page = _build_stats_page(window)
    approvals_page = _build_approvals_page(window)
    reports_page = _build_reports_page(window)

    pages = (
        ("sessions", session_page, "Sessions", "Codex, Operator, and Claude lane activity."),
        ("terminal", terminal_page, "Terminal", "Live launcher output, bridge text, and the highest-signal stats."),
        ("stats", stats_page, "Stats", "Lane status, working tree context, and phone/control-plane health."),
        ("approvals", approvals_page, "Approvals", "Focused review of pending approval packets and decisions."),
        ("reports", reports_page, "Reports", "Readable summaries and staged draft output."),
    )
    window._workbench_surface_indexes = {}  # type: ignore[attr-defined]
    for surface_id, page, label, tooltip in pages:
        index = tabs.addTab(page, label)
        tabs.tabBar().setTabToolTip(index, tooltip)
        window._workbench_surface_indexes[surface_id] = index  # type: ignore[attr-defined]

    tabs.setCurrentIndex(window._workbench_surface_indexes["sessions"])  # type: ignore[attr-defined]
    return tabs, session_page, terminal_page


def _build_log_monitor_tabs(window: object) -> QTabWidget:
    """Render the raw log surfaces without duplicating the top session panes."""
    tabs = QTabWidget()
    tabs.setObjectName("MonitorTabs")
    tabs.setDocumentMode(True)
    tabs.tabBar().setObjectName("MonitorTabBar")
    tabs.tabBar().setExpanding(False)

    monitor_panels = (
        ("bridge", window.raw_bridge_text, "Bridge"),
        ("command_output", window.command_output, "Launcher Output"),
        ("diagnostics", window.dev_log_text, "Diagnostics"),
    )
    window._monitor_tabs = tabs  # type: ignore[attr-defined]
    window._monitor_surface_indexes = {}  # type: ignore[attr-defined]
    for surface_id, widget, label in monitor_panels:
        index = tabs.addTab(widget, label)
        window._monitor_surface_indexes[surface_id] = index  # type: ignore[attr-defined]

    tabs.setCurrentIndex(window._monitor_surface_indexes["command_output"])  # type: ignore[attr-defined]
    return tabs


def _build_stats_page(window: object) -> QWidget:
    """Status-heavy page for lane cards and slower-changing repo context."""
    container = QWidget()
    grid = QGridLayout(container)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setSpacing(8)

    for card in (
        window.workbench_codex_card,
        window.workbench_operator_card,
        window.workbench_claude_card,
    ):
        card.setMaximumHeight(140)

    grid.addWidget(window.workbench_codex_card, 0, 0)
    grid.addWidget(window.workbench_operator_card, 0, 1)
    grid.addWidget(window.workbench_claude_card, 0, 2)
    grid.addWidget(
        window._wrap_in_card(  # type: ignore[attr-defined]
            window._analytics_repo_text,
            "Working Tree",
            "Branch, dirty state, and hotspot paths.",
        ),
        1,
        0,
        1,
        2,
    )
    grid.addWidget(
        window._wrap_in_card(  # type: ignore[attr-defined]
            window._analytics_phone_text,
            "Phone Relay",
            "Mobile/control-plane status and availability.",
        ),
        1,
        2,
    )
    grid.setColumnStretch(0, 3)
    grid.setColumnStretch(1, 3)
    grid.setColumnStretch(2, 2)
    grid.setRowStretch(0, 0)
    grid.setRowStretch(1, 1)
    return container


def _build_approvals_page(window: object) -> QWidget:
    """Approval-focused page with no extra dashboard clutter."""
    return window._approval_container  # type: ignore[attr-defined]


def _build_reports_page(window: object) -> QWidget:
    """Readable digest and draft workspace."""
    return window.activity_workspace  # type: ignore[attr-defined]


def _set_splitter_sizes(splitter: QSplitter, sizes: tuple[int, ...]) -> None:
    total = sum(max(size, 1) for size in sizes)
    if total <= 0:
        return
    scale = 1200
    splitter.setSizes([max(1, int(scale * size / total)) for size in sizes])
