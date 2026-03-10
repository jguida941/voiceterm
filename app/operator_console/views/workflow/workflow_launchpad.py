"""Shared workflow-launcher widget used by Operator Console workflow pages."""

from __future__ import annotations

from ...workflows.workflow_presets import (
    DEFAULT_WORKFLOW_PRESET_ID,
    available_workflow_presets,
    resolve_workflow_preset,
)
from ..shared.widgets import compact_display_text, configure_compact_button

try:
    from PyQt6.QtWidgets import (
        QComboBox,
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


class WorkflowLaunchpad(QWidget if _PYQT_AVAILABLE else object):
    """Shared plan selector and primary workflow actions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.workflow_selector = QComboBox()
        self.workflow_selector.setToolTip(
            "Choose which markdown plan the loop button should drive."
        )
        for preset in available_workflow_presets():
            self.workflow_selector.addItem(preset.label, preset.preset_id)
        default_index = self.workflow_selector.findData(DEFAULT_WORKFLOW_PRESET_ID)
        if default_index >= 0:
            self.workflow_selector.setCurrentIndex(default_index)

        self.workflow_plan_label = QLabel("Plan: dev/active/operator_console.md")
        self.workflow_plan_label.setObjectName("CardStatusLabel")
        self.workflow_plan_label.setWordWrap(True)

        self.workflow_scope_label = QLabel("Scope: MP-359")
        self.workflow_scope_label.setObjectName("RoleBadge")

        self.workflow_summary_label = QLabel(
            "Choose a markdown plan, audit the guard state, then run the loop from the GUI."
        )
        self.workflow_summary_label.setObjectName("CardDetailLabel")
        self.workflow_summary_label.setWordWrap(True)

        self.workflow_steps_label = QLabel(
            "Simple flow: Audit, Run Loop, Dry Run if needed, then Launch Review."
        )
        self.workflow_steps_label.setObjectName("CardDetailLabel")
        self.workflow_steps_label.setWordWrap(True)

        self.workflow_status_label = QLabel("Workflow: Idle")
        self.workflow_status_label.setObjectName("CardStatusLabel")
        self.workflow_status_label.setWordWrap(True)
        self.workflow_status_label.setProperty("statusLevel", "idle")

        self.workflow_detail_label = QLabel(
            "No workflow command has run yet for this scope."
        )
        self.workflow_detail_label.setObjectName("CardDetailLabel")
        self.workflow_detail_label.setWordWrap(True)

        self.audit_button = self._make_button("Audit")
        self.run_loop_button = self._make_button("Run Loop")
        self.dry_run_button = self._make_button("Dry Run")
        self.launch_review_button = self._make_button("Launch Review")
        self.audit_button.setProperty("accentRole", "primary")
        self.run_loop_button.setProperty("accentRole", "primary")
        self.launch_review_button.setProperty("accentRole", "primary")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addWidget(self.workflow_selector)
        root.addWidget(self.workflow_plan_label)

        scope_row = QHBoxLayout()
        scope_row.setSpacing(6)
        scope_row.addWidget(self.workflow_scope_label)
        scope_row.addStretch(1)
        root.addLayout(scope_row)

        root.addWidget(self.workflow_summary_label)
        root.addWidget(self.workflow_steps_label)
        root.addWidget(self.workflow_status_label)
        root.addWidget(self.workflow_detail_label)

        buttons = QGridLayout()
        buttons.setHorizontalSpacing(6)
        buttons.setVerticalSpacing(6)
        buttons.addWidget(self.audit_button, 0, 0)
        buttons.addWidget(self.run_loop_button, 0, 1)
        buttons.addWidget(self.dry_run_button, 1, 0)
        buttons.addWidget(self.launch_review_button, 1, 1)
        root.addLayout(buttons)

        self.set_workflow_preset(resolve_workflow_preset(DEFAULT_WORKFLOW_PRESET_ID))

    def set_workflow_preset(self, preset) -> None:
        """Update the visible plan scope and action hints."""
        self.workflow_plan_label.setText(f"Plan: {preset.plan_doc}")
        self.workflow_plan_label.setToolTip(preset.plan_doc)
        self.workflow_scope_label.setText(f"Scope: {preset.mp_scope}")
        self.workflow_summary_label.setText(
            compact_display_text(preset.summary, limit=180)
        )
        self.workflow_summary_label.setToolTip(preset.summary)
        self.run_loop_button.setToolTip(
            f"Run `devctl swarm_run --continuous` for {preset.plan_doc} ({preset.mp_scope})."
        )
        self.audit_button.setToolTip(
            "Run `devctl orchestrate-status` so active-plan sync, multi-agent sync, and git state are checked from the GUI."
        )
        self.dry_run_button.setToolTip(
            "Run the review-channel launch preflight without opening live Terminal.app sessions."
        )
        self.launch_review_button.setToolTip(
            "Run dry-run preflight first, then open the live Codex/Claude review lanes when the bridge is green."
        )
        self.set_workflow_feedback(
            level="idle",
            label=f"Workflow: {preset.label}",
            detail=(
                f"Scope {preset.mp_scope} is ready. Run Audit to check guards, "
                "or Run Loop to audit first and then launch the continuous plan loop."
            ),
        )

    def set_audience_mode(self, mode: str) -> None:
        """Adjust supporting copy for simple vs technical read modes."""
        technical_mode = mode == "technical"
        self.workflow_steps_label.setText(
            "Fast path: Audit, Run Loop, Dry Run, then Launch Review when the bridge is green."
            if technical_mode
            else "Simple flow: Audit, Run Loop, Dry Run if needed, then Launch Review."
        )

    def set_workflow_feedback(self, *, level: str, label: str, detail: str) -> None:
        """Show the latest workflow-controller state in the launchpad itself."""
        self.workflow_status_label.setText(label)
        self.workflow_status_label.setToolTip(detail)
        self.workflow_status_label.setProperty("statusLevel", level)
        status_style = self.workflow_status_label.style()
        if status_style is not None:
            status_style.unpolish(self.workflow_status_label)
            status_style.polish(self.workflow_status_label)
        self.workflow_status_label.update()

        self.workflow_detail_label.setText(compact_display_text(detail, limit=180))
        self.workflow_detail_label.setToolTip(detail)

    def _make_button(self, label: str) -> QPushButton:
        button = QPushButton(label)
        return configure_compact_button(button)
