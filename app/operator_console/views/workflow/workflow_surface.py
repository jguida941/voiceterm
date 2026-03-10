"""Shared workflow header/footer widgets for the Workbench layout."""

from __future__ import annotations

from ...workflows.workflow_surface_state import WorkflowStageState, WorkflowSurfaceState

try:
    from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object


_STAGE_PREFIX = {
    "active": "[x]",
    "warning": "[!]",
    "idle": "[ ]",
    "stale": "[~]",
}


class WorkflowHeaderBar(QWidget if _PYQT_AVAILABLE else object):
    """Top strip that keeps the shared workflow context always visible."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        frame = QFrame()
        frame.setObjectName("LaneCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel("Shared Workflow")
        title.setObjectName("LaneAgentName")
        layout.addWidget(title)

        top = QHBoxLayout()
        top.setSpacing(6)
        self.slice_label = _role_badge("Slice: n/a")
        self.writer_label = _role_badge("Writer: n/a")
        self.branch_label = _role_badge("Branch: n/a")
        self.swarm_label = _role_badge("Swarm: n/a")
        for label in (
            self.slice_label,
            self.writer_label,
            self.branch_label,
            self.swarm_label,
        ):
            top.addWidget(label)
        top.addStretch(1)
        layout.addLayout(top)

        self.goal_label = QLabel("Goal: n/a")
        self.goal_label.setObjectName("CardDetailLabel")
        self.goal_label.setWordWrap(True)
        layout.addWidget(self.goal_label)

        marker_row = QHBoxLayout()
        marker_row.setSpacing(12)
        self.codex_marker = QLabel("Codex seen/applied: n/a / n/a")
        self.codex_marker.setObjectName("CardDetailLabel")
        self.claude_marker = QLabel("Claude seen/applied: n/a / n/a")
        self.claude_marker.setObjectName("CardDetailLabel")
        marker_row.addWidget(self.codex_marker, stretch=1)
        marker_row.addWidget(self.claude_marker, stretch=1)
        layout.addLayout(marker_row)

        root.addWidget(frame)

    def set_state(self, state: WorkflowSurfaceState) -> None:
        self.slice_label.setText(f"Slice: {state.current_slice}")
        self.writer_label.setText(f"Writer: {state.current_writer}")
        self.branch_label.setText(f"Branch: {state.branch}")
        self.swarm_label.setText(f"Swarm: {state.swarm_health}")
        self.goal_label.setText(f"Goal: {state.shared_goal}")
        self.codex_marker.setText(
            f"Codex seen/applied: {state.codex_last_seen} / {state.codex_last_applied}"
        )
        self.claude_marker.setText(
            f"Claude seen/applied: {state.claude_last_seen} / {state.claude_last_applied}"
        )


class WorkflowTimelineFooter(QWidget if _PYQT_AVAILABLE else object):
    """Bottom footer showing transition stages and the next action."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._stage_labels: dict[str, QLabel] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        frame = QFrame()
        frame.setObjectName("LaneCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel("Workflow Timeline")
        title.setObjectName("LaneAgentName")
        layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(6)
        for stage_id in (
            "posted",
            "read",
            "acked",
            "implementing",
            "tests",
            "reviewed",
            "apply",
        ):
            label = _role_badge(f"[ ] {stage_id.title()}")
            self._stage_labels[stage_id] = label
            row.addWidget(label)
        row.addStretch(1)
        layout.addLayout(row)

        self.next_action_label = QLabel("Next action: refresh snapshot to start.")
        self.next_action_label.setObjectName("CardStatusLabel")
        self.next_action_label.setWordWrap(True)
        layout.addWidget(self.next_action_label)

        root.addWidget(frame)

    def set_state(self, state: WorkflowSurfaceState) -> None:
        for stage in state.stages:
            label = self._stage_labels.get(stage.stage_id)
            if label is None:
                continue
            label.setText(_format_stage(stage))
            label.setToolTip(stage.detail)
        self.next_action_label.setText(f"Next action: {state.next_action}")


def _role_badge(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("RoleBadge")
    return label


def _format_stage(stage: WorkflowStageState) -> str:
    prefix = _STAGE_PREFIX.get(stage.status_level, "[ ]")
    return f"{prefix} {stage.label}"
