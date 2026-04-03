"""Tests for reviewer_follow_packet_guard turn-authority migration."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.review_channel.reviewer_follow_packet_guard import (
    ReviewerFollowPacketDeps,
    ReviewerFollowPacketRequest,
    ReviewerFollowTriggerState,
    _authority_trigger_met,
    _build_trigger_key,
    _legacy_trigger_met,
    _resolve_packet_context,
    maybe_queue_reviewer_follow_packet,
)
from dev.scripts.devctl.review_channel.turn_authority import ReviewerTurnAuthority


def _make_authority(
    *,
    next_turn_required: bool = True,
    next_turn_role: str = "reviewer",
    next_turn_reason: str = "review_follow_up_required",
    attention_status: str = "review_follow_up_required",
    launch_truth: str = "detached_runtime_only",
    current_instruction_revision: str = "abc123",
    reviewer_mode: str = "active_dual_agent",
    effective_reviewer_mode: str = "active_dual_agent",
    review_needed: bool | None = True,
) -> ReviewerTurnAuthority:
    return ReviewerTurnAuthority(
        snapshot_id="test-snap",
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        reviewer_freshness="fresh",
        launch_truth=launch_truth,
        attention_status=attention_status,
        recovery_action_allowed="",
        implementation_blocked=False,
        implementation_block_reason="",
        current_instruction="- Test instruction",
        current_instruction_revision=current_instruction_revision,
        claude_ack_revision="abc123",
        claude_ack_current=True,
        implementer_state_hash="impl_hash_1",
        reviewer_accepted_implementer_state_hash="impl_hash_0",
        reviewed_hash_current=False,
        review_needed=review_needed,
        next_turn_required=next_turn_required,
        next_turn_role=next_turn_role,
        next_turn_reason=next_turn_reason,
    )


def _make_report(
    *,
    review_needed: bool = True,
    attention_status: str = "review_follow_up_required",
    launch_truth: str = "detached_runtime_only",
    reviewer_mode: str = "active_dual_agent",
    current_hash: str = "tree_aaa",
    reviewed_hash: str = "tree_bbb",
    instruction_revision: str = "abc123",
) -> dict[str, object]:
    return {
        "review_needed": review_needed,
        "bridge_liveness": {
            "reviewer_mode": reviewer_mode,
            "effective_reviewer_mode": reviewer_mode,
            "launch_truth": launch_truth,
            "current_instruction_revision": instruction_revision,
            "poll_status_reason": "automation_only",
        },
        "attention": {
            "status": attention_status,
            "recommended_command": "",
        },
        "reviewer_worker": {
            "current_hash": current_hash,
            "reviewed_hash": reviewed_hash,
        },
    }


_SENTINEL_REPORT = object()


def _make_request(
    *,
    report: dict[str, object] | object = _SENTINEL_REPORT,
    turn_authority: ReviewerTurnAuthority | None = None,
    review_channel_path: Path | None = None,
) -> ReviewerFollowPacketRequest:
    repo_root = Path("/tmp/test-repo")
    rcp = review_channel_path or repo_root / "review_channel.md"
    resolved_report = _make_report() if report is _SENTINEL_REPORT else report
    return ReviewerFollowPacketRequest(
        args=SimpleNamespace(session_id="test-sess", plan_id="MP-999", expires_in_minutes=30),
        repo_root=repo_root,
        paths={"review_channel_path": rcp},
        report=resolved_report,
        turn_authority=turn_authority,
    )


class TestAuthorityTriggerMet(unittest.TestCase):
    """Verify _authority_trigger_met uses the turn-authority contract fields."""

    def test_triggers_when_reviewer_turn_required(self):
        auth = _make_authority(next_turn_required=True, next_turn_role="reviewer")
        self.assertTrue(_authority_trigger_met(auth))

    def test_no_trigger_when_implementer_turn(self):
        auth = _make_authority(next_turn_required=True, next_turn_role="implementer")
        self.assertFalse(_authority_trigger_met(auth))

    def test_no_trigger_when_no_turn_required(self):
        auth = _make_authority(next_turn_required=False, next_turn_role="reviewer")
        self.assertFalse(_authority_trigger_met(auth))

    def test_no_trigger_when_inactive(self):
        auth = _make_authority(next_turn_required=False, next_turn_role="")
        self.assertFalse(_authority_trigger_met(auth))


class TestLegacyTriggerMet(unittest.TestCase):
    """Verify _legacy_trigger_met preserves the old local-derivation path."""

    def test_triggers_on_relaunch_required(self):
        bl = {"reviewer_mode": "active_dual_agent", "effective_reviewer_mode": "active_dual_agent"}
        att = {"status": "review_loop_relaunch_required"}
        self.assertTrue(_legacy_trigger_met(bl, att))

    def test_triggers_on_detached_launch_truth(self):
        bl = {
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
            "launch_truth": "detached_runtime_only",
        }
        att = {"status": "healthy"}
        self.assertTrue(_legacy_trigger_met(bl, att))

    def test_no_trigger_when_inactive_mode(self):
        bl = {"reviewer_mode": "single_agent", "effective_reviewer_mode": "single_agent"}
        att = {"status": "review_loop_relaunch_required"}
        self.assertFalse(_legacy_trigger_met(bl, att))

    def test_no_trigger_when_healthy_and_live_launch(self):
        bl = {
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
            "launch_truth": "live_dual_agent",
        }
        att = {"status": "healthy"}
        self.assertFalse(_legacy_trigger_met(bl, att))


class TestBuildTriggerKey(unittest.TestCase):
    """Verify _build_trigger_key reads from authority when present."""

    def test_uses_authority_fields(self):
        auth = _make_authority(
            launch_truth="automation_only",
            current_instruction_revision="rev42",
            attention_status="review_follow_up_required",
        )
        key = _build_trigger_key(
            attention_status="review_follow_up_required",
            reviewer_worker={"current_hash": "h1", "reviewed_hash": "h2"},
            bridge_liveness={"launch_truth": "WRONG", "current_instruction_revision": "WRONG"},
            turn_authority=auth,
        )
        self.assertIn("automation_only", key)
        self.assertIn("rev42", key)
        self.assertNotIn("WRONG", key)

    def test_falls_back_to_bridge_liveness_without_authority(self):
        key = _build_trigger_key(
            attention_status="review_follow_up_required",
            reviewer_worker={"current_hash": "h1", "reviewed_hash": "h2"},
            bridge_liveness={"launch_truth": "detached_runtime_only", "current_instruction_revision": "rev99"},
        )
        self.assertIn("detached_runtime_only", key)
        self.assertIn("rev99", key)


class TestResolvePacketContext(unittest.TestCase):
    """Verify _resolve_packet_context dispatches to the right trigger path."""

    def test_returns_context_with_authority(self):
        auth = _make_authority()
        req = _make_request(turn_authority=auth)
        ctx = _resolve_packet_context(req)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.attention_status, auth.attention_status)

    def test_returns_none_when_authority_says_no_trigger(self):
        auth = _make_authority(next_turn_required=False)
        req = _make_request(turn_authority=auth)
        ctx = _resolve_packet_context(req)
        self.assertIsNone(ctx)

    def test_returns_context_via_legacy_path(self):
        report = _make_report(
            launch_truth="automation_only",
            attention_status="review_follow_up_required",
        )
        req = _make_request(report=report, turn_authority=None)
        ctx = _resolve_packet_context(req)
        self.assertIsNotNone(ctx)

    def test_returns_none_via_legacy_when_not_review_needed(self):
        report = _make_report(review_needed=False)
        req = _make_request(report=report, turn_authority=None)
        ctx = _resolve_packet_context(req)
        self.assertIsNone(ctx)

    def test_returns_none_when_report_dicts_missing(self):
        req = _make_request(report={}, turn_authority=None)
        ctx = _resolve_packet_context(req)
        self.assertIsNone(ctx)


class TestMaybeQueueWithAuthority(unittest.TestCase):
    """Integration: verify maybe_queue_reviewer_follow_packet uses authority when provided."""

    def test_returns_none_when_authority_says_no_trigger(self):
        auth = _make_authority(next_turn_required=False)
        req = _make_request(turn_authority=auth)
        state = ReviewerFollowTriggerState()
        result = maybe_queue_reviewer_follow_packet(request=req, trigger_state=state)
        self.assertIsNone(result)
        self.assertEqual(state.last_trigger_key, "")

    def test_queues_packet_when_authority_triggers(self):
        auth = _make_authority()
        req = _make_request(turn_authority=auth)
        state = ReviewerFollowTriggerState()

        posted_packets = []

        def fake_post(*, repo_root, review_channel_path, artifact_paths, request):
            posted_packets.append(request)
            return (object(), {"packet_id": "pkt-123"})

        def fake_load(*, repo_root, review_channel_path, artifact_paths):
            ns = SimpleNamespace(review_state={"packets": []})
            return ns

        deps = ReviewerFollowPacketDeps(
            load_bundle_fn=fake_load,
            post_packet_fn=fake_post,
        )
        result = maybe_queue_reviewer_follow_packet(
            request=req, trigger_state=state, deps=deps,
        )
        self.assertIsNotNone(result)
        self.assertTrue(result["queued"])
        self.assertEqual(result["packet_id"], "pkt-123")
        self.assertEqual(len(posted_packets), 1)

    def test_deduplicates_existing_pending_packet(self):
        auth = _make_authority(
            attention_status="review_follow_up_required",
            launch_truth="detached_runtime_only",
            current_instruction_revision="abc123",
        )
        report = _make_report()
        req = _make_request(report=report, turn_authority=auth)
        state = ReviewerFollowTriggerState()

        ctx = _resolve_packet_context(req)
        trigger_key = ctx.trigger_key

        def fake_load(*, repo_root, review_channel_path, artifact_paths):
            return SimpleNamespace(review_state={
                "packets": [
                    {
                        "status": "pending",
                        "to_agent": "claude",
                        "requested_action": "restore_reviewer_turn",
                        "body": f"- review_trigger_key: `{trigger_key}`",
                        "packet_id": "existing-pkt",
                    }
                ]
            })

        deps = ReviewerFollowPacketDeps(
            load_bundle_fn=fake_load,
            post_packet_fn=lambda **kw: None,
        )
        result = maybe_queue_reviewer_follow_packet(
            request=req, trigger_state=state, deps=deps,
        )
        self.assertIsNotNone(result)
        self.assertFalse(result["queued"])
        self.assertEqual(result["reason"], "already_pending")
        self.assertEqual(result["packet_id"], "existing-pkt")


if __name__ == "__main__":
    unittest.main()
