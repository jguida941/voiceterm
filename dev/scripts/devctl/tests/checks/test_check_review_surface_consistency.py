"""Tests for review-surface snapshot consistency guard."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.tests.conftest import load_repo_module


class CheckReviewSurfaceConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_repo_module(
            "check_review_surface_consistency",
            "dev/scripts/checks/check_review_surface_consistency.py",
        )

    def test_build_report_passes_when_all_surfaces_share_snapshot_id(self) -> None:
        report = self.script.build_report(
            startup_payload={
                "snapshot_id": "snap-123",
                "push_decision": {"snapshot_id": "snap-123"},
            },
            review_state_payload={
                "snapshot_id": "snap-123",
                "commit_pipeline": {
                    "snapshot_id": "snap-123",
                    "generation_id": "gen-9",
                },
                "_compat": {
                    "doctor": {
                        "snapshot_id": "snap-123",
                        "generation_id": "gen-9",
                    },
                    "bridge_projection": {
                        "metadata": {"snapshot_id": "snap-123"},
                    },
                },
            },
            compact_payload={
                "snapshot_id": "snap-123",
                "push_decision": {"snapshot_id": "snap-123"},
                "doctor": {
                    "snapshot_id": "snap-123",
                    "generation_id": "gen-9",
                },
            },
            commit_pipeline_payload={
                "snapshot_id": "snap-123",
                "generation_id": "gen-9",
            },
            bridge_poll_payload={
                "snapshot_id": "snap-123",
                "effective_reviewer_mode": "active_dual_agent",
                "launch_truth": "live_runtime",
                "attention_status": "healthy",
                "recovery_action_allowed": "",
                "implementation_blocked": False,
                "implementation_block_reason": "",
                "reviewed_hash_current": True,
                "review_needed": False,
                "next_turn_required": False,
                "next_turn_role": "",
                "next_turn_reason": "up_to_date",
            },
            turn_authority_payload={
                "snapshot_id": "snap-123",
                "effective_reviewer_mode": "active_dual_agent",
                "launch_truth": "live_runtime",
                "attention_status": "healthy",
                "recovery_action_allowed": "",
                "implementation_blocked": False,
                "implementation_block_reason": "",
                "reviewed_hash_current": True,
                "review_needed": False,
                "next_turn_required": False,
                "next_turn_role": "",
                "next_turn_reason": "up_to_date",
            },
        )

        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])

    def test_build_report_fails_when_snapshot_ids_diverge(self) -> None:
        report = self.script.build_report(
            startup_payload={
                "snapshot_id": "snap-123",
                "push_decision": {"snapshot_id": "snap-123"},
            },
            review_state_payload={
                "snapshot_id": "snap-123",
                "commit_pipeline": {
                    "snapshot_id": "snap-999",
                    "generation_id": "gen-9",
                },
                "_compat": {
                    "doctor": {
                        "snapshot_id": "snap-123",
                        "generation_id": "gen-8",
                    },
                    "bridge_projection": {
                        "metadata": {"snapshot_id": "snap-123"},
                    },
                },
            },
            compact_payload={
                "snapshot_id": "snap-123",
                "push_decision": {"snapshot_id": "snap-123"},
                "doctor": {
                    "snapshot_id": "snap-123",
                    "generation_id": "gen-9",
                },
            },
            commit_pipeline_payload={
                "snapshot_id": "snap-999",
                "generation_id": "gen-9",
            },
            bridge_poll_payload={
                "snapshot_id": "snap-123",
                "effective_reviewer_mode": "tools_only",
                "launch_truth": "detached_runtime_only",
                "attention_status": "review_loop_relaunch_required",
                "recovery_action_allowed": "launch",
                "implementation_blocked": True,
                "implementation_block_reason": "review_loop_relaunch_required",
                "reviewed_hash_current": True,
                "review_needed": False,
                "next_turn_required": True,
                "next_turn_role": "reviewer",
                "next_turn_reason": "up_to_date",
            },
            turn_authority_payload={
                "snapshot_id": "snap-123",
                "effective_reviewer_mode": "tools_only",
                "launch_truth": "detached_runtime_only",
                "attention_status": "review_loop_relaunch_required",
                "recovery_action_allowed": "launch",
                "implementation_blocked": True,
                "implementation_block_reason": "review_loop_relaunch_required",
                "reviewed_hash_current": True,
                "review_needed": False,
                "next_turn_required": True,
                "next_turn_role": "reviewer",
                "next_turn_reason": "review_loop_relaunch_required",
            },
        )

        self.assertFalse(report["ok"])
        self.assertIn("snapshot_id mismatch", "\n".join(report["errors"]))
        self.assertIn("pipeline generation mismatch", "\n".join(report["errors"]))
        self.assertIn("bridge-poll parity mismatch", "\n".join(report["errors"]))


if __name__ == "__main__":
    unittest.main()
