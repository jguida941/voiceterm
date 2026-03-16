"""Tests for shared runtime review-state contracts."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime import review_state_from_payload


class ReviewStateTests(unittest.TestCase):
    def test_review_state_from_full_projection_normalizes_packets_and_registry(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-03-12T00:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {
                        "plan_id": "MP-355",
                        "session_id": "session-1",
                        "surface_mode": "event-store",
                        "active_lane": "review",
                    },
                    "queue": {"pending_total": 1},
                    "bridge": {
                        "reviewer_mode": "tools_only",
                        "last_codex_poll_utc": "2026-03-12T00:00:00Z",
                        "last_worktree_hash": "abc123",
                        "current_instruction": "continue",
                    },
                    "packets": [
                        {
                            "packet_id": "pkt-1",
                            "from_agent": "codex",
                            "to_agent": "operator",
                            "summary": "Approve push",
                            "body": "Need approval.",
                            "status": "pending",
                            "policy_hint": "operator_approval_required",
                            "requested_action": "git_push",
                            "approval_required": True,
                            "timestamp_utc": "2026-03-12T00:01:00Z",
                        }
                    ],
                },
                "agent_registry": {
                    "timestamp": "2026-03-12T00:02:00Z",
                    "agents": [
                        {
                            "agent_id": "AGENT-1",
                            "display_name": "AGENT-1",
                            "provider": "codex",
                            "lane": "codex",
                            "lane_title": "Codex review",
                            "current_job": "Reviewing slice",
                            "job_state": "active",
                        }
                    ],
                },
                "bridge_liveness": {
                    "overall_state": "fresh",
                    "codex_poll_state": "fresh",
                    "last_codex_poll_age_seconds": 30,
                },
                "attention": {
                    "status": "healthy",
                    "owner": "system",
                    "summary": "Review loop signals are fresh.",
                    "recommended_action": "Continue the scoped review/coding loop.",
                    "recommended_command": "",
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state.review.session_id, "session-1")
        self.assertEqual(state.queue.pending_total, 1)
        self.assertEqual(state.bridge.overall_state, "fresh")
        self.assertEqual(state.bridge.reviewer_mode, "tools_only")
        self.assertEqual(state.attention.status, "healthy")
        self.assertEqual(state.packets[0].posted_at, "2026-03-12T00:01:00Z")
        self.assertEqual(state.pending_approvals()[0].packet_id, "pkt-1")
        self.assertEqual(state.lane_agents("codex")[0].current_job, "Reviewing slice")

    def test_review_state_from_legacy_projection_shape_stays_compatible(self) -> None:
        state = review_state_from_payload(
            {
                "review": {
                    "surface_mode": "markdown-bridge",
                    "session_id": "markdown-bridge",
                    "active_lane": "review",
                },
                "packets": [
                    {
                        "packet_id": "pkt-legacy",
                        "summary": "Legacy packet",
                        "approval_required": True,
                        "status": "pending",
                    }
                ],
                "agent_registry": {
                    "agents": [
                        {
                            "agent_id": "AGENT-9",
                            "provider": "claude",
                            "lane": "claude",
                            "job_state": "assigned",
                        }
                    ]
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state.review.surface_mode, "markdown-bridge")
        self.assertEqual(state.packets[0].packet_id, "pkt-legacy")
        self.assertEqual(state.lane_agents("claude")[0].agent_id, "AGENT-9")


    def test_implementer_completion_stall_survives_parser_roundtrip(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-03-16T02:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "session-stall"},
                    "queue": {"pending_total": 0},
                    "bridge": {
                        "reviewer_mode": "active_dual_agent",
                        "implementer_completion_stall": True,
                    },
                    "packets": [],
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertTrue(state.bridge.implementer_completion_stall)


if __name__ == "__main__":
    unittest.main()
