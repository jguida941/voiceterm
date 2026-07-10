"""Ralph guardrail dashboard widget for the Operator Console.

Displays Ralph loop status, finding breakdown, fix rate progress, and
architecture/severity tables. Uses the same widget patterns as the existing
workflow views.
"""

from __future__ import annotations

from ...state.snapshots.ralph_guardrail_snapshot import RalphGuardrailSnapshot

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QProgressBar,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object

_PHASE_LEVELS = {
    "idle": "idle",
    "running": "active",
    "complete": "active",
    "escalated": "warning",
}


class RalphDashboard(QWidget if _PYQT_AVAILABLE else object):
    """Compact dashboard showing Ralph guardrail loop state."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        card = QFrame()
        card.setObjectName("LaneCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(8)

        # Title row
        title = QLabel("Guardrails")
        title.setObjectName("LaneAgentName")
        card_layout.addWidget(title)
        intro = QLabel("Ralph loop status, fix rate, and guard health.")
        intro.setObjectName("CardDetailLabel")
        intro.setWordWrap(True)
        card_layout.addWidget(intro)

        # Phase and summary row
        card_layout.addWidget(self._build_phase_row())

        # Fix rate progress bar
        card_layout.addWidget(self._build_progress_section())

        # Breakdown tables in a 2-column grid
        card_layout.addWidget(self._build_breakdown_section())

        # Control buttons
        card_layout.addWidget(self._build_controls())

        # Note label at bottom
        self._note_label = QLabel("")
        self._note_label.setObjectName("CardDetailLabel")
        self._note_label.setWordWrap(True)
        self._note_label.setVisible(False)
        card_layout.addWidget(self._note_label)

        card_layout.addStretch(1)
        root.addWidget(card)

    # ── Section builders ─────────────────────────────────────────

    def _build_phase_row(self) -> QWidget:
        """Phase indicator dot, phase label, and summary counts."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._phase_dot = QLabel()
        self._phase_dot.setObjectName("StatusIndicator")
        self._phase_dot.setFixedSize(14, 14)
        self._phase_dot.setProperty("statusLevel", "idle")
        layout.addWidget(self._phase_dot, alignment=Qt.AlignmentFlag.AlignTop)

        self._phase_label = QLabel("Phase: idle")
        self._phase_label.setObjectName("CardStatusLabel")
        layout.addWidget(self._phase_label)

        layout.addStretch(1)

        self._attempt_label = QLabel("Attempt: 0/0")
        self._attempt_label.setObjectName("MutedLabel")
        layout.addWidget(self._attempt_label)

        return container

    def _build_progress_section(self) -> QWidget:
        """Fix rate progress bar with percentage and count labels."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self._total_label = QLabel("Total: 0")
        self._total_label.setObjectName("MutedLabel")
        stats_row.addWidget(self._total_label)
        self._fixed_label = QLabel("Fixed: 0")
        self._fixed_label.setObjectName("MutedLabel")
        stats_row.addWidget(self._fixed_label)
        self._fp_label = QLabel("FP: 0")
        self._fp_label.setObjectName("MutedLabel")
        stats_row.addWidget(self._fp_label)
        self._pending_label = QLabel("Pending: 0")
        self._pending_label.setObjectName("MutedLabel")
        stats_row.addWidget(self._pending_label)
        stats_row.addStretch(1)
        layout.addLayout(stats_row)

        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("RalphFixRateBar")
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(12)
        progress_row.addWidget(self._progress_bar, stretch=1)
        self._rate_label = QLabel("0%")
        self._rate_label.setObjectName("CardStatusLabel")
        self._rate_label.setFixedWidth(48)
        self._rate_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        progress_row.addWidget(self._rate_label)
        layout.addLayout(progress_row)

        return container

    def _build_breakdown_section(self) -> QWidget:
        """Two-column grid with architecture and severity breakdown tables."""
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setSpacing(8)

        arch_label = QLabel("By Architecture")
        arch_label.setObjectName("SectionHeaderLabel")
        grid.addWidget(arch_label, 0, 0)

        self._arch_table = self._make_breakdown_table()
        grid.addWidget(self._arch_table, 1, 0)

        sev_label = QLabel("By Severity")
        sev_label.setObjectName("SectionHeaderLabel")
        grid.addWidget(sev_label, 0, 1)

        self._severity_table = self._make_breakdown_table()
        grid.addWidget(self._severity_table, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        return container

    def _build_controls(self) -> QWidget:
        """Control buttons for Ralph loop management."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        self.start_button = QPushButton("Start Loop")
        self.start_button.setToolTip("Launch a new Ralph guardrail loop cycle.")
        layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setToolTip("Pause the current Ralph loop after the active fix completes.")
        layout.addWidget(self.pause_button)

        self.configure_button = QPushButton("Configure")
        self.configure_button.setToolTip("Open Ralph loop configuration for severity thresholds and auto-fix policy.")
        layout.addWidget(self.configure_button)

        layout.addStretch(1)

        self._branch_label = QLabel("")
        self._branch_label.setObjectName("MutedLabel")
        layout.addWidget(self._branch_label)

        return container

    # ── Public state update ──────────────────────────────────────

    def set_snapshot(self, snap: RalphGuardrailSnapshot) -> None:
        """Push a new Ralph guardrail snapshot into the dashboard."""
        if not snap.available:
            self._set_unavailable(snap.note or "No data available.")
            return

        level = _PHASE_LEVELS.get(snap.phase, "idle")
        self._phase_dot.setProperty("statusLevel", level)
        self._refresh_dot_style()
        self._phase_label.setText(f"Phase: {snap.phase}")
        self._attempt_label.setText(f"Attempt: {snap.attempt}/{snap.max_attempts}")

        self._total_label.setText(f"Total: {snap.total_findings}")
        self._fixed_label.setText(f"Fixed: {snap.fixed_count}")
        self._fp_label.setText(f"FP: {snap.false_positive_count}")
        self._pending_label.setText(f"Pending: {snap.pending_count}")

        rate = int(snap.fix_rate_pct)
        self._progress_bar.setValue(min(rate, 100))
        self._rate_label.setText(f"{snap.fix_rate_pct:.0f}%")

        self._populate_table(self._arch_table, snap.by_architecture)
        self._populate_table(self._severity_table, snap.by_severity)

        branch_text = f"Branch: {snap.branch}" if snap.branch else ""
        if snap.last_run_timestamp:
            branch_text = f"{branch_text}  |  Last: {snap.last_run_timestamp}" if branch_text else f"Last: {snap.last_run_timestamp}"
        self._branch_label.setText(branch_text)

        if snap.note:
            self._note_label.setText(snap.note)
            self._note_label.setVisible(True)
        else:
            self._note_label.setVisible(False)

    # ── Internal helpers ─────────────────────────────────────────

    def _set_unavailable(self, message: str) -> None:
        """Reset all display elements to an unavailable state."""
        self._phase_dot.setProperty("statusLevel", "idle")
        self._refresh_dot_style()
        self._phase_label.setText("Phase: offline")
        self._attempt_label.setText("Attempt: 0/0")
        self._total_label.setText("Total: 0")
        self._fixed_label.setText("Fixed: 0")
        self._fp_label.setText("FP: 0")
        self._pending_label.setText("Pending: 0")
        self._progress_bar.setValue(0)
        self._rate_label.setText("0%")
        self._arch_table.setRowCount(0)
        self._severity_table.setRowCount(0)
        self._branch_label.setText("")
        self._note_label.setText(message)
        self._note_label.setVisible(True)

    def _refresh_dot_style(self) -> None:
        style = self._phase_dot.style()
        if style is not None:
            style.unpolish(self._phase_dot)
            style.polish(self._phase_dot)
        self._phase_dot.update()

    @staticmethod
    def _make_breakdown_table() -> QTableWidget:
        """Create a compact 3-column table for breakdown display."""
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Name", "Total", "Fixed"])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.verticalHeader().setVisible(False)
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.setMaximumHeight(140)
        return table

    @staticmethod
    def _populate_table(
        table: QTableWidget,
        data: tuple[tuple[str, int, int], ...],
    ) -> None:
        """Fill a breakdown table with (name, total, fixed) rows."""
        table.setRowCount(len(data))
        for row_idx, (name, total, fixed) in enumerate(data):
            table.setItem(row_idx, 0, QTableWidgetItem(name))
            total_item = QTableWidgetItem(str(total))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row_idx, 1, total_item)
            fixed_item = QTableWidgetItem(str(fixed))
            fixed_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row_idx, 2, fixed_item)
