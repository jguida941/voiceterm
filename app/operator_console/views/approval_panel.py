"""Self-contained approval queue panel for the Operator Console.

Replaces the inline approval list/buttons with a richer widget that shows
per-item severity badges, a detail pane on selection, and a risk indicator
derived from policy_hint keywords.
"""

from __future__ import annotations

from ..collaboration.context_pack_refs import context_pack_ref_lines
from ..state.core.models import ApprovalRequest
from ..state.presentation.presentation_state import classify_approval_risk

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QSizePolicy,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object


if _PYQT_AVAILABLE:

    class ApprovalQueuePanel(QWidget):
        """Self-contained approval queue with rich rows and a detail pane.

        API contract for the parent window:
        - ``set_approvals(approvals)`` — push new data each poll cycle
        - ``selected_approval()`` — read the currently highlighted item
        - ``decision_requested`` signal — emitted when Approve/Deny is clicked,
          carrying ``(decision, approval, note)`` so the parent can write the
          artifact without reaching into this widget's internals.
        """

        decision_requested = pyqtSignal(str, object, str)

        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self._approvals_by_id: dict[str, ApprovalRequest] = {}

            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(6)

            # Header
            header = QHBoxLayout()
            header.setSpacing(8)
            self._header_label = QLabel("Pending Approvals")
            self._header_label.setObjectName("SectionHeaderLabel")
            header.addWidget(self._header_label)
            self._count_badge = QLabel("0")
            self._count_badge.setObjectName("ApprovalCountBadge")
            self._count_badge.setFixedSize(24, 24)
            self._count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.addWidget(self._count_badge)
            header.addStretch(1)
            root.addLayout(header)

            # Splitter: list (top/left) + detail pane (bottom/right)
            splitter = QSplitter(Qt.Orientation.Vertical)
            splitter.setHandleWidth(3)
            splitter.setChildrenCollapsible(False)

            # Approval list
            self._list = QListWidget()
            self._list.setObjectName("ApprovalList")
            self._list.currentItemChanged.connect(self._on_selection_changed)
            splitter.addWidget(self._list)

            # Detail pane
            self._detail_pane = QFrame()
            self._detail_pane.setObjectName("ApprovalDetailPane")
            detail_layout = QVBoxLayout(self._detail_pane)
            detail_layout.setContentsMargins(12, 10, 12, 10)
            detail_layout.setSpacing(6)

            self._detail_header = QLabel("Select an approval to view details")
            self._detail_header.setObjectName("ApprovalDetailHeader")
            self._detail_header.setWordWrap(True)
            detail_layout.addWidget(self._detail_header)

            self._flow_label = QLabel("")
            self._flow_label.setObjectName("ApprovalFlowLabel")
            detail_layout.addWidget(self._flow_label)

            self._action_label = QLabel("")
            self._action_label.setObjectName("ApprovalActionLabel")
            detail_layout.addWidget(self._action_label)

            self._risk_indicator = QLabel("")
            self._risk_indicator.setObjectName("ApprovalRiskIndicator")
            self._risk_indicator.setProperty("riskLevel", "unknown")
            self._risk_indicator.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            detail_layout.addWidget(self._risk_indicator)

            self._body_text = QLabel("")
            self._body_text.setObjectName("ApprovalBodyText")
            self._body_text.setWordWrap(True)
            self._body_text.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            detail_layout.addWidget(self._body_text, stretch=1)

            self._evidence_label = QLabel("")
            self._evidence_label.setObjectName("ApprovalEvidenceLabel")
            self._evidence_label.setWordWrap(True)
            detail_layout.addWidget(self._evidence_label)

            splitter.addWidget(self._detail_pane)
            splitter.setStretchFactor(0, 2)
            splitter.setStretchFactor(1, 3)

            root.addWidget(splitter, stretch=1)

            # Decision controls
            controls = QVBoxLayout()
            controls.setSpacing(4)

            self._note_input = QLineEdit()
            self._note_input.setPlaceholderText("Operator note (optional)")
            controls.addWidget(self._note_input)

            self._mode_hint = QLabel(
                "Typed wrapper mode: this records repo-visible operator decision "
                "artifacts. Direct devctl review-channel ack|apply|dismiss is not "
                "available yet."
            )
            self._mode_hint.setObjectName("ApprovalModeHint")
            self._mode_hint.setWordWrap(True)
            controls.addWidget(self._mode_hint)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(4)
            self._approve_btn = QPushButton("Approve")
            self._approve_btn.setObjectName("SmallActionButton")
            self._approve_btn.setProperty("accentRole", "primary")
            self._approve_btn.setEnabled(False)
            self._approve_btn.clicked.connect(lambda: self._emit_decision("approve"))
            btn_row.addWidget(self._approve_btn)

            self._deny_btn = QPushButton("Deny")
            self._deny_btn.setObjectName("SmallActionButton")
            self._deny_btn.setProperty("accentRole", "danger")
            self._deny_btn.setEnabled(False)
            self._deny_btn.clicked.connect(lambda: self._emit_decision("deny"))
            btn_row.addWidget(self._deny_btn)

            controls.addLayout(btn_row)
            root.addLayout(controls)

            self._update_detail_pane(None)

        # ── Public API ────────────────────────────────────────

        def set_approvals(self, approvals: tuple[ApprovalRequest, ...]) -> None:
            """Replace the queue contents, preserving selection if possible."""
            prev_id = self._selected_packet_id()
            self._approvals_by_id = {a.packet_id: a for a in approvals}

            self._list.blockSignals(True)
            self._list.clear()
            restore_row: int | None = None

            for idx, approval in enumerate(approvals):
                risk = classify_approval_risk(approval.policy_hint)
                label = f"{approval.packet_id}  {approval.summary}"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, approval.packet_id)
                # Embed risk level for potential QSS styling
                item.setData(Qt.ItemDataRole.UserRole + 1, risk)
                self._list.addItem(item)
                if approval.packet_id == prev_id:
                    restore_row = idx

            self._list.blockSignals(False)

            if restore_row is not None:
                self._list.setCurrentRow(restore_row)
            else:
                self._on_selection_changed(self._list.currentItem(), None)

            self._count_badge.setText(str(len(approvals)))
            self.setVisible(True)

        def selected_approval(self) -> ApprovalRequest | None:
            """Return the currently selected approval, or None."""
            packet_id = self._selected_packet_id()
            if packet_id is None:
                return None
            return self._approvals_by_id.get(packet_id)

        @property
        def note_text(self) -> str:
            return self._note_input.text()

        def clear_note(self) -> None:
            self._note_input.clear()

        # ── Internal ──────────────────────────────────────────

        def _selected_packet_id(self) -> str | None:
            current = self._list.currentItem()
            if current is None:
                return None
            return current.data(Qt.ItemDataRole.UserRole)

        def _on_selection_changed(
            self,
            current: QListWidgetItem | None,
            _previous: QListWidgetItem | None,
        ) -> None:
            approval = self.selected_approval()
            enabled = approval is not None
            self._approve_btn.setEnabled(enabled)
            self._deny_btn.setEnabled(enabled)
            self._update_detail_pane(approval)

        def _update_detail_pane(self, approval: ApprovalRequest | None) -> None:
            if approval is None:
                if self._approvals_by_id:
                    self._detail_header.setText("Select an approval to view details")
                    self._body_text.setText("")
                else:
                    self._detail_header.setText("0 Pending")
                    self._body_text.setText(
                        "Approval requests will appear here when the bridge emits them."
                    )
                self._flow_label.setText("")
                self._action_label.setText("")
                self._risk_indicator.setText("")
                self._risk_indicator.setProperty("riskLevel", "unknown")
                self._refresh_risk_indicator_style()
                self._evidence_label.setText("")
                return

            risk = classify_approval_risk(approval.policy_hint)
            risk_display = risk.upper()

            self._detail_header.setText(
                f"[{approval.packet_id}] {approval.summary}"
            )
            self._flow_label.setText(
                f"{approval.from_agent}  \u2192  {approval.to_agent}"
            )
            self._action_label.setText(
                f"Action: {approval.requested_action}  |  Policy: {approval.policy_hint}"
            )
            self._risk_indicator.setText(f"Risk: {risk_display}")
            self._risk_indicator.setProperty("riskLevel", risk)
            self._refresh_risk_indicator_style()

            body = approval.body.strip() if approval.body else "(no body)"
            self._body_text.setText(body)

            detail_sections: list[str] = []
            if approval.evidence_refs:
                refs = "\n".join(f"  \u2022 {ref}" for ref in approval.evidence_refs)
                detail_sections.append(f"Evidence:\n{refs}")
            if approval.context_pack_refs:
                refs = "\n".join(
                    f"  \u2022 {line}"
                    for line in context_pack_ref_lines(approval.context_pack_refs)
                )
                detail_sections.append(f"Context Packs:\n{refs}")
            self._evidence_label.setText("\n\n".join(detail_sections))

        def _refresh_risk_indicator_style(self) -> None:
            style = self._risk_indicator.style()
            if style is not None:
                style.unpolish(self._risk_indicator)
                style.polish(self._risk_indicator)
            self._risk_indicator.update()

        def _emit_decision(self, decision: str) -> None:
            approval = self.selected_approval()
            if approval is None:
                return
            self.decision_requested.emit(
                decision, approval, self._note_input.text()
            )

else:
    # Stub for environments without PyQt6
    class ApprovalQueuePanel:  # type: ignore[no-redef]
        """Stub when PyQt6 is not installed."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def set_approvals(self, approvals: object) -> None:
            pass

        def selected_approval(self) -> None:
            return None

        @property
        def note_text(self) -> str:
            return ""

        def clear_note(self) -> None:
            pass
