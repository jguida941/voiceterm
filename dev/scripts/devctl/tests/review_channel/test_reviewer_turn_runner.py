"""Tests for the portable controller-owned reviewer turn runner.

Covers wake detection, context assembly, result validation, and
provider-agnostic portability guarantees.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.review_channel.reviewer_turn_runner import (
    NEXT_BLOCKED,
    NEXT_CONTINUE,
    NEXT_WAIT,
    PUBLICATION_BLOCKED,
    PUBLICATION_IMPLEMENTER_OWNS,
    PUBLICATION_REVIEWER_OWNS,
    TURN_BLOCKED,
    TURN_COMPLETED,
    TURN_ERROR,
    TURN_NO_ACTION,
    WAKE_OPERATOR_REQUEST,
    WAKE_PENDING_PACKET,
    WAKE_SCHEDULED,
    WAKE_TREE_CHANGED,
    ReviewerTurnContext,
    ReviewerTurnResult,
    ReviewerWakeSignal,
    build_reviewer_turn_context,
    detect_reviewer_wake,
    validate_turn_result,
)
from dev.scripts.devctl.review_channel.reviewer_worker import ReviewerWorkerTick
from dev.scripts.devctl.review_channel.turn_authority import ReviewerTurnAuthority


# ── Helpers ────────────────────────────────────────────────────


def _make_authority(
    *,
    next_turn_required: bool = True,
    next_turn_role: str = "reviewer",
    next_turn_reason: str = "review_follow_up_required",
    reviewer_mode: str = "active_dual_agent",
    effective_reviewer_mode: str = "active_dual_agent",
) -> ReviewerTurnAuthority:
    return ReviewerTurnAuthority(
        snapshot_id="test-snap",
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        reviewer_freshness="fresh",
        launch_truth="detached_runtime_only",
        attention_status="review_follow_up_required",
        recovery_action_allowed="",
        implementation_blocked=False,
        implementation_block_reason="",
        current_instruction="- Review the changes",
        current_instruction_revision="rev-001",
        claude_ack_revision="rev-001",
        claude_ack_current=True,
        implementer_state_hash="impl_hash_1",
        reviewer_accepted_implementer_state_hash="impl_hash_0",
        reviewed_hash_current=False,
        review_needed=True,
        next_turn_required=next_turn_required,
        next_turn_role=next_turn_role,
        next_turn_reason=next_turn_reason,
    )


def _make_wake(
    kind: str = WAKE_PENDING_PACKET,
    detail: str = "1 pending packet(s) for codex",
    **kwargs,
) -> ReviewerWakeSignal:
    return ReviewerWakeSignal(kind=kind, detail=detail, **kwargs)


def _make_packet(
    packet_id: str = "rev_pkt_100",
    to_agent: str = "codex",
    status: str = "pending",
    kind: str = "finding",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "to_agent": to_agent,
        "from_agent": "claude",
        "status": status,
        "kind": kind,
        "summary": f"Test packet {packet_id}",
    }


# ── Wake detection tests ──────────────────────────────────────


class TestDetectReviewerWake(unittest.TestCase):
    """Test reviewer wake signal detection."""

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_wake_on_pending_packets(self, mock_load):
        mock_load.return_value = (_make_packet(),)
        signal = detect_reviewer_wake(
            repo_root=Path("/fake"),
            bridge_path=Path("/fake/bridge.md"),
            reviewer_provider="codex",
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.kind, WAKE_PENDING_PACKET)
        self.assertEqual(signal.pending_packet_ids, ("rev_pkt_100",))

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_wake_on_tree_change(self, mock_load):
        mock_load.return_value = ()
        tick = ReviewerWorkerTick(
            state="review_needed",
            review_needed=True,
            reviewed_hash="aaa",
            current_hash="bbb",
            reviewer_mode="active_dual_agent",
            detail="Tree has changed since last review",
        )
        signal = detect_reviewer_wake(
            repo_root=Path("/fake"),
            bridge_path=Path("/fake/bridge.md"),
            reviewer_provider="codex",
            worker_tick=tick,
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.kind, WAKE_TREE_CHANGED)
        self.assertEqual(signal.tree_hash_before, "aaa")
        self.assertEqual(signal.tree_hash_after, "bbb")

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_no_wake_when_up_to_date(self, mock_load):
        mock_load.return_value = ()
        tick = ReviewerWorkerTick(
            state="up_to_date",
            review_needed=False,
            reviewed_hash="aaa",
            current_hash="aaa",
            reviewer_mode="active_dual_agent",
            detail="Tree matches reviewed hash",
        )
        signal = detect_reviewer_wake(
            repo_root=Path("/fake"),
            bridge_path=Path("/fake/bridge.md"),
            reviewer_provider="codex",
            worker_tick=tick,
        )
        self.assertIsNone(signal)

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_ignores_packets_for_other_agent(self, mock_load):
        mock_load.return_value = (_make_packet(to_agent="claude"),)
        tick = ReviewerWorkerTick(
            state="up_to_date",
            review_needed=False,
            reviewed_hash="aaa",
            current_hash="aaa",
            reviewer_mode="active_dual_agent",
            detail="Tree matches reviewed hash",
        )
        signal = detect_reviewer_wake(
            repo_root=Path("/fake"),
            bridge_path=Path("/fake/bridge.md"),
            reviewer_provider="codex",
            worker_tick=tick,
        )
        self.assertIsNone(signal)

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_custom_reviewer_provider(self, mock_load):
        mock_load.return_value = (
            _make_packet(to_agent="gemini"),
        )
        signal = detect_reviewer_wake(
            repo_root=Path("/fake"),
            bridge_path=Path("/fake/bridge.md"),
            reviewer_provider="gemini",
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.kind, WAKE_PENDING_PACKET)


# ── Context assembly tests ─────────────────────────────────────


class TestBuildReviewerTurnContext(unittest.TestCase):
    """Test reviewer turn context assembly."""

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_builds_context_when_reviewer_turn_required(self, mock_load):
        mock_load.return_value = ()
        authority = _make_authority()
        wake = _make_wake()
        ctx = build_reviewer_turn_context(
            wake_signal=wake,
            authority=authority,
            repo_root=Path("/fake"),
        )
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.reviewer_provider, "codex")
        self.assertEqual(ctx.implementer_provider, "claude")
        self.assertEqual(ctx.interaction_mode, "local_terminal")

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_returns_none_when_no_turn_required(self, mock_load):
        mock_load.return_value = ()
        authority = _make_authority(next_turn_required=False)
        wake = _make_wake()
        ctx = build_reviewer_turn_context(
            wake_signal=wake,
            authority=authority,
            repo_root=Path("/fake"),
        )
        self.assertIsNone(ctx)

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_returns_none_when_implementer_turn(self, mock_load):
        mock_load.return_value = ()
        authority = _make_authority(next_turn_role="implementer")
        wake = _make_wake()
        ctx = build_reviewer_turn_context(
            wake_signal=wake,
            authority=authority,
            repo_root=Path("/fake"),
        )
        self.assertIsNone(ctx)

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_operator_override_ignores_authority(self, mock_load):
        mock_load.return_value = ()
        authority = _make_authority(
            next_turn_required=False,
            next_turn_role="implementer",
        )
        wake = _make_wake(kind=WAKE_OPERATOR_REQUEST)
        ctx = build_reviewer_turn_context(
            wake_signal=wake,
            authority=authority,
            repo_root=Path("/fake"),
        )
        self.assertIsNotNone(ctx)

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_custom_providers(self, mock_load):
        mock_load.return_value = ()
        authority = _make_authority()
        wake = _make_wake()
        ctx = build_reviewer_turn_context(
            wake_signal=wake,
            authority=authority,
            repo_root=Path("/fake"),
            reviewer_provider="gemini",
            implementer_provider="cursor",
            interaction_mode="remote_control",
        )
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.reviewer_provider, "gemini")
        self.assertEqual(ctx.implementer_provider, "cursor")
        self.assertEqual(ctx.interaction_mode, "remote_control")

    @patch(
        "dev.scripts.devctl.review_channel.reviewer_turn_runner.load_pending_packets"
    )
    def test_context_to_dict_is_serializable(self, mock_load):
        mock_load.return_value = (_make_packet(),)
        authority = _make_authority()
        wake = _make_wake()
        ctx = build_reviewer_turn_context(
            wake_signal=wake,
            authority=authority,
            repo_root=Path("/fake"),
        )
        self.assertIsNotNone(ctx)
        d = ctx.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["reviewer_provider"], "codex")
        self.assertEqual(d["pending_packet_count"], 1)


# ── Result validation tests ────────────────────────────────────


class TestValidateTurnResult(unittest.TestCase):
    """Test reviewer turn result validation."""

    def test_valid_completed_result(self):
        result = ReviewerTurnResult(
            status=TURN_COMPLETED,
            next_state=NEXT_WAIT,
            detail="Reviewed successfully",
        )
        self.assertEqual(validate_turn_result(result), [])

    def test_valid_result_with_packets(self):
        result = ReviewerTurnResult(
            status=TURN_COMPLETED,
            emitted_packets=(
                {"kind": "finding", "summary": "Found an issue"},
            ),
            next_state=NEXT_CONTINUE,
            detail="One finding emitted",
        )
        self.assertEqual(validate_turn_result(result), [])

    def test_valid_publication_decisions(self):
        for decision in (
            "", PUBLICATION_IMPLEMENTER_OWNS,
            PUBLICATION_REVIEWER_OWNS, PUBLICATION_BLOCKED,
        ):
            result = ReviewerTurnResult(
                status=TURN_COMPLETED,
                publication_decision=decision,
            )
            self.assertEqual(
                validate_turn_result(result), [],
                f"Failed for decision: {decision!r}",
            )

    def test_invalid_status(self):
        result = ReviewerTurnResult(status="unknown_status")
        errors = validate_turn_result(result)
        self.assertTrue(any("Unknown turn status" in e for e in errors))

    def test_invalid_next_state(self):
        result = ReviewerTurnResult(
            status=TURN_COMPLETED, next_state="invalid",
        )
        errors = validate_turn_result(result)
        self.assertTrue(any("Unknown next state" in e for e in errors))

    def test_invalid_publication_decision(self):
        result = ReviewerTurnResult(
            status=TURN_COMPLETED,
            publication_decision="bogus",
        )
        errors = validate_turn_result(result)
        self.assertTrue(any("Unknown publication decision" in e for e in errors))

    def test_packet_missing_kind(self):
        result = ReviewerTurnResult(
            status=TURN_COMPLETED,
            emitted_packets=({"summary": "No kind field"},),
        )
        errors = validate_turn_result(result)
        self.assertTrue(any("missing 'kind'" in e for e in errors))

    def test_packet_missing_summary(self):
        result = ReviewerTurnResult(
            status=TURN_COMPLETED,
            emitted_packets=({"kind": "finding"},),
        )
        errors = validate_turn_result(result)
        self.assertTrue(any("missing 'summary'" in e for e in errors))

    def test_non_dict_packet_rejected(self):
        result = ReviewerTurnResult(
            status=TURN_COMPLETED,
            emitted_packets=("not_a_dict",),
        )
        errors = validate_turn_result(result)
        self.assertTrue(any("not a dict" in e for e in errors))

    def test_all_valid_statuses_pass(self):
        for status in (TURN_COMPLETED, TURN_BLOCKED, TURN_ERROR, TURN_NO_ACTION):
            result = ReviewerTurnResult(status=status)
            errors = validate_turn_result(result)
            status_errors = [e for e in errors if "turn status" in e]
            self.assertEqual(
                status_errors, [],
                f"Status {status!r} should be valid",
            )


# ── Serialization round-trip ───────────────────────────────────


class TestSerialization(unittest.TestCase):
    """Verify all dataclasses serialize cleanly."""

    def test_wake_signal_to_dict(self):
        signal = ReviewerWakeSignal(
            kind=WAKE_TREE_CHANGED,
            detail="Tree changed",
            tree_hash_before="aaa",
            tree_hash_after="bbb",
        )
        d = signal.to_dict()
        self.assertEqual(d["kind"], WAKE_TREE_CHANGED)
        self.assertEqual(d["tree_hash_before"], "aaa")

    def test_turn_result_to_dict(self):
        result = ReviewerTurnResult(
            status=TURN_COMPLETED,
            publication_decision=PUBLICATION_IMPLEMENTER_OWNS,
            publication_target_sha="abc123",
            detail="Done",
        )
        d = result.to_dict()
        self.assertEqual(d["status"], TURN_COMPLETED)
        self.assertEqual(d["publication_decision"], PUBLICATION_IMPLEMENTER_OWNS)


if __name__ == "__main__":
    unittest.main()
