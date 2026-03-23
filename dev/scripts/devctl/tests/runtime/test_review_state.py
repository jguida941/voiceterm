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
        self.assertEqual(state.current_session.current_instruction, "continue")
        self.assertEqual(state.bridge.overall_state, "fresh")
        self.assertEqual(state.bridge.reviewer_mode, "tools_only")
        self.assertEqual(state.attention.status, "healthy")
        self.assertEqual(state.packets[0].posted_at, "2026-03-12T00:01:00Z")
        self.assertEqual(state.pending_approvals()[0].packet_id, "pkt-1")
        self.assertEqual(state.lane_agents("codex")[0].current_job, "Reviewing slice")

    def test_review_state_parses_plan_review_packet_fields(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-03-19T00:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "plan-review"},
                    "queue": {"pending_total": 1},
                    "bridge": {"reviewer_mode": "tools_only"},
                    "packets": [
                        {
                            "packet_id": "pkt-plan-1",
                            "kind": "plan_patch_review",
                            "from_agent": "codex",
                            "to_agent": "operator",
                            "summary": "Patch plan progress log",
                            "body": "Append the accepted proof-pass note.",
                            "status": "pending",
                            "policy_hint": "operator_approval_required",
                            "requested_action": "patch_plan",
                            "approval_required": True,
                            "timestamp_utc": "2026-03-19T00:01:00Z",
                            "target_kind": "plan",
                            "target_ref": "plan://MP-377/platform_authority_loop",
                            "target_revision": "sha256:abc123",
                            "anchor_refs": [
                                "progress:proof_pass",
                                "checklist:phase_1",
                            ],
                            "guidance_refs": [
                                "probe_design_smells@dev/active/platform_authority_loop.md:12"
                            ],
                            "intake_ref": "intake://session-2026-03-19",
                            "mutation_op": "append_progress_log",
                        }
                    ],
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        packet = state.packets[0]
        self.assertEqual(packet.kind, "plan_patch_review")
        self.assertEqual(packet.target_kind, "plan")
        self.assertEqual(packet.target_ref, "plan://MP-377/platform_authority_loop")
        self.assertEqual(packet.target_revision, "sha256:abc123")
        self.assertEqual(
            packet.anchor_refs,
            ("progress:proof_pass", "checklist:phase_1"),
        )
        self.assertEqual(
            packet.guidance_refs,
            ("probe_design_smells@dev/active/platform_authority_loop.md:12",),
        )
        self.assertEqual(packet.intake_ref, "intake://session-2026-03-19")
        self.assertEqual(packet.mutation_op, "append_progress_log")

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

    def test_event_backed_full_projection_parses_same_shared_contract_fields(self) -> None:
        bridge_state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-03-16T03:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {
                        "plan_id": "MP-377",
                        "session_id": "markdown-bridge",
                        "surface_mode": "markdown-bridge",
                        "active_lane": "review",
                    },
                    "queue": {
                        "pending_total": 1,
                        "derived_next_instruction": "review the live tranche",
                    },
                    "current_session": {
                        "current_instruction": "review the live tranche",
                        "current_instruction_revision": "abc123def456",
                        "implementer_status": "active",
                        "implementer_ack": "acknowledged",
                        "implementer_ack_revision": "abc123def456",
                        "implementer_ack_state": "current",
                        "open_findings": "none",
                        "last_reviewed_scope": "MP-377",
                    },
                    "bridge": {
                        "reviewer_mode": "active_dual_agent",
                        "last_codex_poll_utc": "2026-03-16T03:00:00Z",
                        "current_instruction": "review the live tranche",
                        "claude_status": "active",
                        "claude_ack": "acknowledged",
                        "claude_ack_current": True,
                        "current_instruction_revision": "abc123def456",
                        "claude_ack_revision": "abc123def456",
                    },
                    "packets": [
                        {
                            "packet_id": "rev_pkt_0001",
                            "from_agent": "operator",
                            "to_agent": "codex",
                            "summary": "review the live tranche",
                            "status": "pending",
                            "approval_required": False,
                            "timestamp_utc": "2026-03-16T03:00:00Z",
                        }
                    ],
                },
                "agent_registry": {
                    "timestamp": "2026-03-16T03:00:00Z",
                    "agents": [
                        {
                            "agent_id": "AGENT-1",
                            "provider": "codex",
                            "lane": "codex",
                            "job_state": "reviewing",
                        }
                    ],
                },
                "bridge_liveness": {
                    "overall_state": "fresh",
                    "codex_poll_state": "fresh",
                    "last_codex_poll_age_seconds": 0,
                },
                "attention": {
                    "status": "healthy",
                    "owner": "system",
                    "summary": "Review loop signals are fresh.",
                    "recommended_action": "Continue",
                    "recommended_command": "",
                },
            }
        )
        event_state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-03-16T03:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {
                        "plan_id": "MP-377",
                        "session_id": "local-review",
                        "surface_mode": "event-backed",
                        "active_lane": "review",
                    },
                    "queue": {
                        "pending_total": 1,
                        "derived_next_instruction": "review the live tranche",
                    },
                    "current_session": {
                        "current_instruction": "review the live tranche",
                        "current_instruction_revision": "abc123def456",
                        "implementer_status": "waiting",
                        "implementer_ack": "acknowledged",
                        "implementer_ack_revision": "",
                        "implementer_ack_state": "unknown",
                        "open_findings": "1 pending review packet(s)",
                        "last_reviewed_scope": "MP-377",
                    },
                    "bridge": {
                        "reviewer_mode": "tools_only",
                        "last_codex_poll_utc": "2026-03-16T03:00:00Z",
                        "current_instruction": "review the live tranche",
                        "claude_status": "waiting",
                        "claude_ack": "acknowledged",
                        "claude_ack_current": True,
                        "current_instruction_revision": "abc123def456",
                        "claude_ack_revision": "abc123def456",
                    },
                    "packets": [
                        {
                            "packet_id": "rev_pkt_0001",
                            "from_agent": "operator",
                            "to_agent": "codex",
                            "summary": "review the live tranche",
                            "status": "pending",
                            "approval_required": False,
                            "timestamp_utc": "2026-03-16T03:00:00Z",
                        }
                    ],
                },
                "agent_registry": {
                    "timestamp": "2026-03-16T03:00:00Z",
                    "agents": [
                        {
                            "agent_id": "AGENT-1",
                            "provider": "codex",
                            "lane": "codex",
                            "job_state": "reviewing",
                        }
                    ],
                },
                "bridge_liveness": {
                    "overall_state": "fresh",
                    "codex_poll_state": "fresh",
                    "last_codex_poll_age_seconds": 0,
                },
                "attention": {
                    "status": "inactive",
                    "owner": "system",
                    "summary": "Event-backed review state is available without live bridge enforcement.",
                    "recommended_action": "Continue from the structured event state.",
                    "recommended_command": "",
                },
                "service_identity": {
                    "service_id": "review-channel:sha256:test",
                    "project_id": "sha256:test",
                },
                "attach_auth_policy": {
                    "attach_scope": "repo_worktree_local",
                },
            }
        )

        self.assertIsNotNone(bridge_state)
        self.assertIsNotNone(event_state)
        assert bridge_state is not None
        assert event_state is not None
        self.assertEqual(bridge_state.queue.pending_total, event_state.queue.pending_total)
        self.assertEqual(
            bridge_state.queue.derived_next_instruction,
            event_state.queue.derived_next_instruction,
        )
        self.assertEqual(
            bridge_state.current_session.current_instruction,
            event_state.current_session.current_instruction,
        )
        self.assertEqual(
            bridge_state.current_session.current_instruction_revision,
            "abc123def456",
        )
        self.assertEqual(event_state.current_session.implementer_ack_state, "unknown")
        self.assertEqual(
            bridge_state.bridge.current_instruction,
            event_state.bridge.current_instruction,
        )
        self.assertEqual(bridge_state.bridge.overall_state, event_state.bridge.overall_state)
        self.assertEqual(bridge_state.packets[0].packet_id, event_state.packets[0].packet_id)
        self.assertEqual(
            bridge_state.registry.agents[0].agent_id,
            event_state.registry.agents[0].agent_id,
        )
        self.assertEqual(event_state.attention.status, "inactive")


if __name__ == "__main__":
    unittest.main()
