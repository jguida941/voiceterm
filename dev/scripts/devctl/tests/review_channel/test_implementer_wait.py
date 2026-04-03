"""Focused tests for implementer-side bounded wait with runtime degradation."""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel._wait import (
    ImplementerWaitSnapshot,
    _baseline_wait_outcome,
    _poll_wait_outcome,
    _reviewer_runtime_degraded,
    _reviewer_unhealthy,
)
from dev.scripts.devctl.commands.review_channel._wait_reporting import (
    STOP_REASON_REVIEWER_RUNTIME_DEGRADED,
    STOP_REASON_REVIEWER_UNHEALTHY,
    finalize_implementer_wait_report,
)


def _snapshot(
    *,
    exit_code: int = 0,
    review_needed: bool = True,
    claude_ack_current: bool = True,
    attention_status: str = "healthy",
    attention_summary: str = "",
    attention_recommended_action: str = "",
    next_turn_role: str = "reviewer",
    next_turn_reason: str = "reviewer_wait_state",
    effective_reviewer_mode: str = "active_dual_agent",
    recovery_action_allowed: str = "",
    bridge_liveness: dict | None = None,
) -> ImplementerWaitSnapshot:
    bl = bridge_liveness or {
        "effective_reviewer_mode": effective_reviewer_mode,
        "reviewer_mode": "active_dual_agent",
    }
    return ImplementerWaitSnapshot(
        report={"bridge_liveness": bl, "review_needed": review_needed},
        exit_code=exit_code,
        reviewer_token="tok",
        review_needed=review_needed,
        claude_ack_current=claude_ack_current,
        current_instruction_revision="rev1",
        next_turn_role=next_turn_role,
        next_turn_reason=next_turn_reason,
        attention_status=attention_status,
        attention_summary=attention_summary,
        attention_recommended_action=attention_recommended_action,
        latest_pending_packet_id="",
        effective_reviewer_mode=effective_reviewer_mode,
        recovery_action_allowed=recovery_action_allowed,
    )


_DEFAULT_TIMEOUT_SECONDS = 60
_DEFAULT_INTERVAL_SECONDS = 5


class TestReviewerRuntimeDegraded(unittest.TestCase):
    """Verify _reviewer_runtime_degraded detects typed downgrade signals."""

    def test_tools_only_is_degraded(self):
        snap = _snapshot(effective_reviewer_mode="tools_only")
        self.assertTrue(_reviewer_runtime_degraded(snap))

    def test_single_agent_is_degraded(self):
        snap = _snapshot(effective_reviewer_mode="single_agent")
        self.assertTrue(_reviewer_runtime_degraded(snap))

    def test_active_dual_agent_not_degraded(self):
        snap = _snapshot(effective_reviewer_mode="active_dual_agent")
        self.assertFalse(_reviewer_runtime_degraded(snap))

    def test_relaunch_required_attention_is_degraded(self):
        snap = _snapshot(
            effective_reviewer_mode="active_dual_agent",
            attention_status="review_loop_relaunch_required",
        )
        self.assertTrue(_reviewer_runtime_degraded(snap))

    def test_implementer_relaunch_required_is_degraded(self):
        snap = _snapshot(
            effective_reviewer_mode="active_dual_agent",
            attention_status="implementer_relaunch_required",
        )
        self.assertTrue(_reviewer_runtime_degraded(snap))

    def test_empty_effective_mode_not_degraded(self):
        """Empty effective_reviewer_mode falls through to _reviewer_unhealthy."""
        snap = _snapshot(effective_reviewer_mode="")
        self.assertFalse(_reviewer_runtime_degraded(snap))

    def test_healthy_attention_not_degraded(self):
        snap = _snapshot(
            effective_reviewer_mode="active_dual_agent",
            attention_status="healthy",
        )
        self.assertFalse(_reviewer_runtime_degraded(snap))


class TestBaselinePrefersDegradedOverUnhealthy(unittest.TestCase):
    """When runtime is degraded, baseline should return degraded, not unhealthy."""

    def test_degraded_tools_only_returns_degraded_stop_reason(self):
        snap = _snapshot(
            effective_reviewer_mode="tools_only",
            attention_status="review_loop_relaunch_required",
            recovery_action_allowed="python3 dev/scripts/devctl.py review-channel --action launch",
        )
        outcome = _baseline_wait_outcome(
            snap,
            timeout_seconds=_DEFAULT_TIMEOUT_SECONDS,
            interval_seconds=_DEFAULT_INTERVAL_SECONDS,
        )
        self.assertIsNotNone(outcome)
        self.assertEqual(outcome.stop_reason, "reviewer_runtime_degraded")
        self.assertEqual(outcome.exit_code, 1)

    def test_unhealthy_heartbeat_missing_still_returns_unhealthy(self):
        """When mode is healthy but heartbeat is gone, keep the unhealthy path."""
        snap = _snapshot(
            effective_reviewer_mode="",
            attention_status="reviewer_heartbeat_missing",
            exit_code=0,
            bridge_liveness={
                "reviewer_mode": "active_dual_agent",
            },
        )
        outcome = _baseline_wait_outcome(
            snap,
            timeout_seconds=_DEFAULT_TIMEOUT_SECONDS,
            interval_seconds=_DEFAULT_INTERVAL_SECONDS,
        )
        self.assertIsNotNone(outcome)
        self.assertEqual(outcome.stop_reason, "reviewer_unhealthy")


class TestPollPrefersDegradedOverUnhealthy(unittest.TestCase):
    """When runtime degrades mid-poll, the poll outcome should be degraded."""

    def test_mid_poll_degradation_returns_degraded(self):
        baseline = _snapshot(effective_reviewer_mode="active_dual_agent")
        current = _snapshot(
            effective_reviewer_mode="tools_only",
            attention_status="review_loop_relaunch_required",
        )
        outcome = _poll_wait_outcome(
            baseline=baseline,
            current=current,
            polls_observed=2,
            timeout_seconds=_DEFAULT_TIMEOUT_SECONDS,
            interval_seconds=_DEFAULT_INTERVAL_SECONDS,
        )
        self.assertIsNotNone(outcome)
        self.assertEqual(outcome.stop_reason, "reviewer_runtime_degraded")


class TestDegradedReportSurfacesRecovery(unittest.TestCase):
    """The finalized report should surface recovery_action_allowed for degraded stops."""

    def test_report_includes_recovery_command(self):
        recovery_cmd = "python3 dev/scripts/devctl.py review-channel --action launch --terminal terminal-app"
        snap = _snapshot(
            effective_reviewer_mode="tools_only",
            attention_status="review_loop_relaunch_required",
            recovery_action_allowed=recovery_cmd,
        )
        outcome = _baseline_wait_outcome(
            snap,
            timeout_seconds=_DEFAULT_TIMEOUT_SECONDS,
            interval_seconds=_DEFAULT_INTERVAL_SECONDS,
        )

        args = SimpleNamespace(action="implementer-wait", format="json")
        report, exit_code = finalize_implementer_wait_report(
            baseline=snap,
            current=snap,
            args=args,
            outcome=outcome,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            report["wait_state"]["stop_reason"],
            STOP_REASON_REVIEWER_RUNTIME_DEGRADED,
        )
        self.assertEqual(report["wait_recovery_action_allowed"], recovery_cmd)
        self.assertTrue(
            any("degraded" in str(e).lower() for e in report.get("errors", [])),
            f"Expected 'degraded' in errors, got: {report.get('errors')}",
        )
        error_text = report["errors"][0]
        self.assertIn("Recovery command:", error_text)
        self.assertIn(recovery_cmd, error_text)

    def test_report_without_recovery_command_omits_suffix(self):
        snap = _snapshot(
            effective_reviewer_mode="tools_only",
            attention_status="review_loop_relaunch_required",
            recovery_action_allowed="",
        )
        outcome = _baseline_wait_outcome(
            snap,
            timeout_seconds=_DEFAULT_TIMEOUT_SECONDS,
            interval_seconds=_DEFAULT_INTERVAL_SECONDS,
        )

        args = SimpleNamespace(action="implementer-wait", format="json")
        report, _ = finalize_implementer_wait_report(
            baseline=snap,
            current=snap,
            args=args,
            outcome=outcome,
        )

        error_text = report["errors"][0]
        self.assertNotIn("Recovery command:", error_text)
        self.assertIn("degraded", error_text.lower())


class TestLegitimateWaitMarkersPreserved(unittest.TestCase):
    """Legitimate reviewer-owned wait states must not trigger degraded exit."""

    def test_reviewer_wait_state_proceeds_to_poll(self):
        """When mode is active and reviewer says 'hold steady', no immediate exit."""
        snap = _snapshot(
            effective_reviewer_mode="active_dual_agent",
            attention_status="healthy",
            next_turn_role="reviewer",
            next_turn_reason="reviewer_wait_state",
        )
        outcome = _baseline_wait_outcome(
            snap,
            timeout_seconds=_DEFAULT_TIMEOUT_SECONDS,
            interval_seconds=_DEFAULT_INTERVAL_SECONDS,
        )
        self.assertIsNone(outcome, "Should enter poll loop, not exit immediately")

    def test_healthy_review_needed_proceeds_to_poll(self):
        snap = _snapshot(
            effective_reviewer_mode="active_dual_agent",
            attention_status="review_follow_up_required",
            review_needed=True,
            next_turn_role="implementer",
            next_turn_reason="some_reason",
        )
        outcome = _baseline_wait_outcome(
            snap,
            timeout_seconds=_DEFAULT_TIMEOUT_SECONDS,
            interval_seconds=_DEFAULT_INTERVAL_SECONDS,
        )
        self.assertIsNone(outcome, "Should enter poll loop when review is needed")


if __name__ == "__main__":
    unittest.main()
