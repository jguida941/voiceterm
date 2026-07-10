"""Tests for the ApprovalQueuePanel widget."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.operator_console.state.core.models import ApprovalRequest, ContextPackRef

try:
    from PyQt6.QtWidgets import QApplication

    _PYQT_AVAILABLE = True
except ImportError:
    QApplication = None
    _PYQT_AVAILABLE = False


def _make_approval(
    *,
    packet_id: str = "pkt-1",
    policy_hint: str = "review",
    summary: str = "test approval",
    from_agent: str = "AGENT-1",
    to_agent: str = "AGENT-9",
    requested_action: str = "merge",
    body: str = "Please review this change.",
    evidence_refs: tuple[str, ...] = ("file1.py", "file2.py"),
    context_pack_refs: tuple[ContextPackRef, ...] = (),
) -> ApprovalRequest:
    return ApprovalRequest(
        packet_id=packet_id,
        from_agent=from_agent,
        to_agent=to_agent,
        summary=summary,
        body=body,
        policy_hint=policy_hint,
        requested_action=requested_action,
        status="pending",
        evidence_refs=evidence_refs,
        context_pack_refs=context_pack_refs,
    )


@unittest.skipIf(not _PYQT_AVAILABLE, "PyQt6 is not installed")
class ApprovalQueuePanelTests(unittest.TestCase):
    """Widget tests requiring a running QApplication."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def _make_panel(self):  # noqa: ANN202
        from app.operator_console.views.approval_panel import ApprovalQueuePanel

        return ApprovalQueuePanel()

    def test_empty_approvals_keep_panel_visible_with_zero_state(self) -> None:
        panel = self._make_panel()
        panel.set_approvals(())
        self.assertTrue(panel.isVisible())
        self.assertEqual(panel._count_badge.text(), "0")
        self.assertEqual(panel._detail_header.text(), "0 Pending")
        self.assertIn("appear here", panel._body_text.text())
        self.assertFalse(panel._approve_btn.isEnabled())
        self.assertFalse(panel._deny_btn.isEnabled())

    def test_set_approvals_shows_panel(self) -> None:
        panel = self._make_panel()
        panel.set_approvals((_make_approval(),))
        self.assertTrue(panel.isVisible())

    def test_panel_explains_wrapper_fallback_mode(self) -> None:
        panel = self._make_panel()
        self.assertIn("repo-visible operator decision artifacts", panel._mode_hint.text())
        self.assertIn("ack|apply|dismiss", panel._mode_hint.text())

    def test_count_badge_reflects_queue_size(self) -> None:
        panel = self._make_panel()
        approvals = (
            _make_approval(packet_id="pkt-1"),
            _make_approval(packet_id="pkt-2"),
            _make_approval(packet_id="pkt-3"),
        )
        panel.set_approvals(approvals)
        self.assertEqual(panel._count_badge.text(), "3")

    def test_selected_approval_returns_none_when_empty(self) -> None:
        panel = self._make_panel()
        panel.set_approvals(())
        self.assertIsNone(panel.selected_approval())

    def test_empty_panel_keeps_unknown_risk_indicator(self) -> None:
        panel = self._make_panel()
        panel.set_approvals(())
        self.assertEqual(panel._risk_indicator.text(), "")
        self.assertEqual(panel._risk_indicator.property("riskLevel"), "unknown")

    def test_selection_enables_buttons(self) -> None:
        panel = self._make_panel()
        panel.set_approvals((_make_approval(),))
        panel._list.setCurrentRow(0)
        self.assertTrue(panel._approve_btn.isEnabled())
        self.assertTrue(panel._deny_btn.isEnabled())

    def test_detail_pane_populates_on_selection(self) -> None:
        panel = self._make_panel()
        approval = _make_approval(
            packet_id="pkt-42",
            summary="merge feature branch",
            from_agent="AGENT-2",
            to_agent="AGENT-10",
            requested_action="merge",
            policy_hint="staging-approval",
            body="This is the body text.",
            evidence_refs=("test_a.py", "test_b.py"),
        )
        panel.set_approvals((approval,))
        panel._list.setCurrentRow(0)

        self.assertIn("pkt-42", panel._detail_header.text())
        self.assertIn("AGENT-2", panel._flow_label.text())
        self.assertIn("AGENT-10", panel._flow_label.text())
        self.assertIn("merge", panel._action_label.text())
        self.assertIn("MEDIUM", panel._risk_indicator.text())
        self.assertEqual(panel._risk_indicator.property("riskLevel"), "medium")
        self.assertEqual(panel._risk_indicator.styleSheet(), "")
        self.assertEqual(panel._body_text.text(), "This is the body text.")
        self.assertIn("test_a.py", panel._evidence_label.text())

    def test_detail_pane_shows_context_pack_refs(self) -> None:
        panel = self._make_panel()
        approval = _make_approval(
            context_pack_refs=(
                ContextPackRef(
                    pack_kind="task_pack",
                    pack_ref=".voiceterm/memory/exports/task_pack.json",
                    adapter_profile="canonical",
                ),
            ),
        )
        panel.set_approvals((approval,))
        panel._list.setCurrentRow(0)

        self.assertIn("Context Packs", panel._evidence_label.text())
        self.assertIn("task_pack", panel._evidence_label.text())
        self.assertIn("task_pack.json", panel._evidence_label.text())

    def test_decision_signal_fires(self) -> None:
        panel = self._make_panel()
        approval = _make_approval(packet_id="pkt-99")
        panel.set_approvals((approval,))
        panel._list.setCurrentRow(0)
        panel._note_input.setText("looks good")

        received: list[tuple[str, object, str]] = []
        panel.decision_requested.connect(
            lambda d, a, n: received.append((d, a, n))
        )
        panel._approve_btn.click()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], "approve")
        self.assertEqual(received[0][1].packet_id, "pkt-99")
        self.assertEqual(received[0][2], "looks good")

    def test_selection_preserved_across_refresh(self) -> None:
        panel = self._make_panel()
        a1 = _make_approval(packet_id="pkt-A")
        a2 = _make_approval(packet_id="pkt-B")
        panel.set_approvals((a1, a2))
        panel._list.setCurrentRow(1)
        self.assertEqual(panel.selected_approval().packet_id, "pkt-B")

        # Re-set with same data — selection should survive
        panel.set_approvals((a1, a2))
        sel = panel.selected_approval()
        self.assertIsNotNone(sel)
        self.assertEqual(sel.packet_id, "pkt-B")


if __name__ == "__main__":
    unittest.main()
