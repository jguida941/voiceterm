"""Tests for shared runtime review-state contracts."""

from __future__ import annotations

from hashlib import sha256
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
                    "collaboration": {
                        "schema_version": 1,
                        "contract_id": "CollaborationSession",
                        "session_id": "session-1",
                        "plan_id": "MP-355",
                        "status": "live",
                        "reviewer_mode": "tools_only",
                        "operator_mode": "manual",
                        "lead_agent": "codex",
                        "review_agent": "codex",
                        "coding_agent": "claude",
                        "current_slice": "continue",
                        "topology_mode": "dual_agent",
                        "work_ownership_mode": "concurrent_writer_conflict",
                        "peer_review": {
                            "current_instruction": "continue",
                            "current_instruction_revision": "",
                            "open_findings": "",
                            "implementer_status": "active",
                            "implementer_ack": "",
                            "implementer_ack_state": "unknown",
                        },
                        "ownership": {
                            "status": "concurrent_writer_activity",
                            "summary": "Dirty paths fall outside the claimed slice while typed peer activity is still present.",
                            "scope_source": "current_session.current_instruction",
                            "outside_scope_dirty_paths": [
                                "dev/scripts/devctl/review_channel/session_state_hints.py"
                            ],
                            "live_agents": ["codex", "claude"],
                            "peer_activity_detected": True,
                            "concurrent_writer_detected": True,
                        },
                        "arbitration": {
                            "status": "clear",
                            "summary": "",
                            "owner": "",
                        },
                        "restart": {
                            "status": "live",
                            "resumable": True,
                            "source": "session_metadata",
                        },
                        "ready_gates": [],
                        "role_assignments": [],
                        "participants": [],
                        "delegated_work": [],
                    },
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
        self.assertEqual(state.collaboration.contract_id, "CollaborationSession")
        self.assertEqual(state.collaboration.review_agent, "codex")
        self.assertEqual(state.collaboration.topology_mode, "dual_agent")
        self.assertEqual(
            state.collaboration.work_ownership_mode,
            "concurrent_writer_conflict",
        )
        self.assertEqual(
            state.collaboration.ownership.status,
            "concurrent_writer_activity",
        )
        self.assertEqual(state.bridge.overall_state, "fresh")
        self.assertEqual(state.bridge.reviewer_mode, "tools_only")
        self.assertEqual(state.attention.status, "healthy")
        self.assertEqual(state.packets[0].posted_at, "2026-03-12T00:01:00Z")
        self.assertEqual(state.pending_approvals()[0].packet_id, "pkt-1")
        self.assertEqual(state.lane_agents("codex")[0].current_job, "Reviewing slice")

    def test_review_state_parses_review_candidate_record(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-04-05T00:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "candidate-session"},
                    "queue": {"pending_total": 0},
                    "bridge": {"reviewer_mode": "active_dual_agent"},
                    "review_candidate": {
                        "candidate_id": "review-candidate-123",
                        "instruction_revision": "rev-123",
                        "artifact_kind": "dirty_tree",
                        "base_sha": "aaaa",
                        "head_sha": "bbbb",
                        "worktree_hash": "c" * 64,
                        "changed_paths": ["tracked.txt"],
                        "ready_for_review": True,
                        "valid": True,
                        "implementer_state_hash": "state-123",
                    },
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        assert state.review_candidate is not None
        self.assertEqual(state.review_candidate.candidate_id, "review-candidate-123")
        self.assertEqual(state.review_candidate.artifact_kind, "dirty_tree")
        self.assertEqual(state.review_candidate.changed_paths, ("tracked.txt",))

    def test_review_state_parses_top_level_push_authorization_record(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-04-05T00:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "push-auth-session"},
                    "queue": {"pending_total": 0},
                    "bridge": {"reviewer_mode": "active_dual_agent"},
                    "push_authorization": {
                        "authorization_id": "push-auth-123",
                        "pipeline_id": "pipeline-123",
                        "generation_id": "gen-123",
                        "authorized_head_sha": "deadbeef",
                        "approved_target_identity": "tree-receipt-123",
                        "review_verdict": "approved",
                        "approval_mode": "commit_pipeline_approval",
                        "guard_action_id": "quality.guard_bundle",
                        "guard_status": "pass",
                        "guard_reason": "all_green",
                    },
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        assert state.push_authorization is not None
        self.assertEqual(state.push_authorization.authorization_id, "push-auth-123")
        self.assertEqual(state.push_authorization.authorized_head_sha, "deadbeef")
        self.assertEqual(
            state.push_authorization.approval_mode,
            "commit_pipeline_approval",
        )

    def test_review_state_parses_coordination_snapshot(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-04-08T00:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "coordination-session"},
                    "queue": {"pending_total": 0},
                    "bridge": {"reviewer_mode": "single_agent"},
                    "coordination": {
                        "contract_id": "CoordinationSnapshot",
                        "current_slice": "Wire dashboard parity from typed coordination.",
                        "declared_topology": "multi_agent_orchestrated",
                        "observed_topology": "single_agent",
                        "recommended_topology": "single_agent",
                        "fanout_posture": "planned_scaffolding_only",
                        "safe_to_fanout": False,
                        "worktree_strategy": "isolated_worker_worktrees",
                        "resync_required": True,
                        "resync_reasons": ["declared_topology:multi_agent_orchestrated"],
                        "actors": [
                            {
                                "actor_id": "codex",
                                "provider": "codex",
                                "role": "reviewer",
                                "presence": "live",
                            }
                        ],
                    },
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        assert state.coordination is not None
        self.assertEqual(
            state.coordination.current_slice,
            "Wire dashboard parity from typed coordination.",
        )
        self.assertEqual(state.coordination.recommended_topology, "single_agent")
        self.assertEqual(state.coordination.actors[0].actor_id, "codex")

    def test_review_state_parses_remote_control_attachment(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-04-09T00:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "remote-session"},
                    "queue": {"pending_total": 0},
                    "bridge": {"reviewer_mode": "single_agent"},
                    "reviewer_runtime": {
                        "remote_control_attachment": {
                            "provider": "claude",
                            "role": "implementer",
                            "attachment_id": "remote-attach-1",
                            "session_name": "VoiceTerm Bridge Loop",
                            "remote_session_id": "session_abc123",
                            "session_url": "https://claude.ai/code/session_abc123",
                            "status": "attached",
                        }
                    },
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        attachment = state.reviewer_runtime.remote_control_attachment
        self.assertIsNotNone(attachment)
        assert attachment is not None
        self.assertEqual(attachment.provider, "claude")
        self.assertEqual(attachment.remote_session_id, "session_abc123")
        self.assertEqual(attachment.status, "attached")

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

    def test_review_state_parses_commit_approval_packet_fields(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-04-03T00:00:00Z",
                "snapshot_id": "snap-123",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "runtime-approval"},
                    "queue": {"pending_total": 1},
                    "bridge": {"reviewer_mode": "active_dual_agent"},
                    "packets": [
                        {
                            "packet_id": "pkt-commit-1",
                            "kind": "commit_approval",
                            "from_agent": "operator",
                            "to_agent": "system",
                            "summary": "Approve governed commit pipeline",
                            "body": "Operator approved the staged snapshot.",
                            "status": "applied",
                            "policy_hint": "operator_approval_required",
                            "requested_action": "approve_commit_pipeline",
                            "approval_required": False,
                            "posted_at": "2026-04-03T00:01:00Z",
                            "target_kind": "runtime",
                            "target_ref": "remote_commit_pipeline:pipeline-123",
                            "target_revision": "gen-9",
                            "pipeline_generation": "gen-9",
                            "staged_snapshot_hash": "tree-123",
                            "guard_results_summary": (
                                "bundle.tooling pass; review-channel doctor "
                                "still reports runtime_missing"
                            ),
                        }
                    ],
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        packet = state.packets[0]
        self.assertEqual(packet.kind, "commit_approval")
        self.assertEqual(packet.target_kind, "runtime")
        self.assertEqual(
            packet.target_ref,
            "remote_commit_pipeline:pipeline-123",
        )
        self.assertEqual(packet.pipeline_generation, "gen-9")
        self.assertEqual(packet.staged_snapshot_hash, "tree-123")
        self.assertEqual(
            packet.guard_results_summary,
            "bundle.tooling pass; review-channel doctor still reports runtime_missing",
        )

    def test_review_state_parses_action_request_delivery_fields(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-04-11T00:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "action-delivery"},
                    "queue": {"pending_total": 1},
                    "bridge": {"reviewer_mode": "single_agent"},
                    "packets": [
                        {
                            "packet_id": "pkt-action-1",
                            "kind": "action_request",
                            "from_agent": "claude",
                            "to_agent": "codex",
                            "summary": "Run the focused proof",
                            "body": "python3 dev/scripts/checks/check_review_channel_bridge.py",
                            "status": "acked",
                            "policy_hint": "safe_auto_apply",
                            "requested_action": "run_check",
                            "approval_required": False,
                            "posted_at": "2026-04-11T00:01:00Z",
                            "delivery_emitted_at_utc": "2026-04-11T00:01:00Z",
                            "delivery_observed_at_utc": "2026-04-11T00:01:05Z",
                            "delivery_observed_by": "codex",
                            "execution_started_at_utc": "2026-04-11T00:01:08Z",
                            "execution_started_by": "codex",
                        }
                    ],
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        packet = state.packets[0]
        self.assertEqual(packet.delivery_emitted_at_utc, "2026-04-11T00:01:00Z")
        self.assertEqual(packet.delivery_observed_at_utc, "2026-04-11T00:01:05Z")
        self.assertEqual(packet.delivery_observed_by, "codex")
        self.assertEqual(packet.execution_started_at_utc, "2026-04-11T00:01:08Z")
        self.assertEqual(packet.execution_started_by, "codex")

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

    def test_missing_reviewer_mode_defaults_to_single_agent(self) -> None:
        state = review_state_from_payload(
            {
                "review_state": {
                    "review": {"session_id": "session-legacy"},
                    "queue": {"pending_total": 0},
                    "bridge": {},
                }
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state.bridge.reviewer_mode, "single_agent")
        self.assertEqual(state.commit_pipeline.state, "push_blocked")
        self.assertEqual(state.commit_pipeline.blocked_reason, "pipeline_unavailable")

    def test_review_state_parses_remote_commit_pipeline_contract(self) -> None:
        state = review_state_from_payload(
            {
                "review_state": {
                    "review": {"session_id": "session-pipeline"},
                    "queue": {"pending_total": 0},
                    "bridge": {"reviewer_mode": "active_dual_agent"},
                    "commit_pipeline": {
                        "pipeline_id": "pipeline-123",
                        "state": "operator_approval_pending",
                        "requested_by": "operator",
                        "branch": "feature/remote",
                        "remote": "origin",
                        "intent": {
                            "staged_tree_hash": "tree-123",
                            "staged_path_count": 2,
                            "staged_paths": [
                                "dev/scripts/devctl/runtime/review_state_models.py",
                                "dev/scripts/devctl/review_channel/parser.py",
                            ],
                            "diff_summary": "Land the read-only pipeline projection slice.",
                            "commit_message_draft": "Add remote commit pipeline state projection",
                            "push_requested": True,
                            "guard_profile": "ci",
                            "validation_plan": {
                                "plan_id": "validation-plan-123",
                                "bundle_id": "ci",
                                "staged_tree_hash": "tree-123",
                                "selected_paths": [
                                    "dev/scripts/devctl/runtime/review_state_models.py",
                                    "dev/scripts/devctl/review_channel/parser.py",
                                ],
                                "proof_level": "publish_ready",
                                "checkpoint_required": True,
                                "push_requested": True,
                            },
                            "work_intake_ref": "intake://remote-commit-slice",
                        },
                        "guard_action_id": "quality.guard_bundle",
                        "guard_result": {
                            "schema_version": 1,
                            "contract_id": "ActionResult",
                            "action_id": "quality.guard_bundle",
                            "ok": True,
                            "status": "pass",
                            "artifact_paths": [
                                "dev/reports/review_channel/latest/guard.json"
                            ],
                        },
                        "validation_receipt": {
                            "receipt_id": "validation-receipt-123",
                            "plan_id": "validation-plan-123",
                            "bundle_id": "ci",
                            "staged_tree_hash": "tree-123",
                            "action_id": "quality.guard_bundle",
                            "status": "pass",
                            "checkpoint_sufficient": True,
                            "push_sufficient": True,
                            "emitted_at_utc": "2026-04-03T00:30:00Z",
                        },
                        "reviewer_runtime_generation": "runtime-gen-7",
                        "approval_packet_id": "packet-approve",
                        "decision_packet_id": "packet-decision",
                        "approval_state": "approved",
                        "commit_action_id": "vcs.commit",
                        "commit_result": {
                            "schema_version": 1,
                            "contract_id": "ActionResult",
                            "action_id": "vcs.commit",
                            "ok": True,
                            "status": "pass",
                        },
                        "commit_sha": "abc123def456",
                        "push_action_id": "vcs.push",
                        "push_result": {
                            "schema_version": 1,
                            "contract_id": "ActionResult",
                            "action_id": "vcs.push",
                            "ok": False,
                            "status": "unknown",
                        },
                        "push_report_path": "dev/reports/review_channel/latest/push.json",
                        "blocked_reason": "",
                        "recovery_action_allowed": "python3 dev/scripts/devctl.py review-channel --action recover",
                        "generation_id": "gen-9",
                        "approval_expires_at_utc": "2026-04-03T01:00:00Z",
                        "approved_target_identity": "tree-123:gen-9",
                        "snapshot_id": "snap-123",
                    },
                }
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state.snapshot_id, "snap-123")
        self.assertEqual(state.commit_pipeline.pipeline_id, "pipeline-123")
        self.assertEqual(state.commit_pipeline.intent.staged_tree_hash, "tree-123")
        self.assertEqual(
            state.commit_pipeline.intent.staged_paths,
            (
                "dev/scripts/devctl/runtime/review_state_models.py",
                "dev/scripts/devctl/review_channel/parser.py",
            ),
        )
        self.assertEqual(
            state.commit_pipeline.guard_result.action_id,
            "quality.guard_bundle",
        )
        self.assertEqual(
            state.commit_pipeline.intent.validation_plan.plan_id,
            "validation-plan-123",
        )
        self.assertEqual(
            state.commit_pipeline.validation_receipt.receipt_id,
            "validation-receipt-123",
        )
        self.assertEqual(
            state.commit_pipeline.approval_expires_at_utc,
            "2026-04-03T01:00:00Z",
        )
        self.assertEqual(
            state.commit_pipeline.approved_target_identity,
            "tree-123:gen-9",
        )
        self.assertEqual(state.commit_pipeline.snapshot_id, "snap-123")

    def test_reviewer_runtime_contract_prefers_typed_publish_clear(self) -> None:
        state = review_state_from_payload(
            {
                "review_state": {
                    "review": {"session_id": "session-runtime-contract"},
                    "queue": {"pending_total": 0},
                    "bridge": {
                        "reviewer_mode": "active_dual_agent",
                        "effective_reviewer_mode": "active_dual_agent",
                        "review_accepted": False,
                    },
                    "reviewer_runtime": {
                        "reviewer_mode": "active_dual_agent",
                        "effective_reviewer_mode": "active_dual_agent",
                        "reviewer_freshness": "fresh",
                        "stale_reason": "",
                        "last_poll": {
                            "last_codex_poll_utc": "2026-04-02T00:00:00Z",
                            "last_codex_poll_age_seconds": 12,
                        },
                        "rollover": {
                            "rollover_id": "rollover-123",
                            "ack_pending": False,
                            "trigger": "peer-stale",
                        },
                        "session_owner": {
                            "provider": "codex",
                            "session_name": "codex-review",
                            "session_pid": 42,
                            "terminal_window_id": 7,
                            "script_path": "/tmp/codex-review.sh",
                        },
                        "recovery_action_allowed": "",
                        "review_acceptance": {
                            "current_verdict": "Reviewer-accepted.",
                            "open_findings": "- none",
                            "review_accepted": True,
                            "reviewer_accepted_implementer_state_hash": "impl-hash-123",
                        },
                        "publish_clear": True,
                    },
                }
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertTrue(state.reviewer_runtime.publish_clear)
        self.assertTrue(state.reviewer_runtime.review_acceptance.review_accepted)
        self.assertEqual(
            state.reviewer_runtime.review_acceptance.reviewer_accepted_implementer_state_hash,
            "impl-hash-123",
        )
        self.assertEqual(state.reviewer_runtime.session_owner.session_pid, 42)
        self.assertEqual(state.reviewer_runtime.rollover.rollover_id, "rollover-123")

    def test_reviewer_runtime_contract_falls_back_to_bridge_fields(self) -> None:
        state = review_state_from_payload(
            {
                "review_state": {
                    "review": {"session_id": "session-runtime-fallback"},
                    "queue": {"pending_total": 0},
                    "bridge": {
                        "reviewer_mode": "active_dual_agent",
                        "review_accepted": True,
                        "open_findings": "- none",
                    },
                    "current_session": {
                        "open_findings": "- none",
                    },
                },
                "attention": {
                    "status": "healthy",
                    "recommended_command": "",
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertTrue(state.reviewer_runtime.review_acceptance.review_accepted)
        self.assertTrue(state.reviewer_runtime.publish_clear)

    def test_recovery_assessment_normalizes_attention_projection(self) -> None:
        state = review_state_from_payload(
            {
                "review_state": {
                    "review": {"session_id": "session-recovery-authority"},
                    "queue": {"pending_total": 0},
                    "bridge": {"reviewer_mode": "active_dual_agent"},
                },
                "attention": {
                    "status": "healthy",
                    "owner": "operator",
                    "summary": "stale local summary",
                    "recommended_action": "use old command",
                    "recommended_command": "legacy-command",
                },
                "recovery_assessment": {
                    "diagnosis": {
                        "status": "implementer_state_reset_required",
                        "root_cause": "Claude Ack is stale for the live instruction.",
                    },
                    "decision": {
                        "action_id": "reset_implementer_state",
                        "command": "python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --terminal none --format md",
                        "execution_owner": "reviewer",
                        "rationale": "Reset the implementer state before resuming work.",
                    },
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state.attention.status, "implementer_state_reset_required")
        self.assertEqual(state.attention.owner, "reviewer")
        self.assertEqual(
            state.attention.summary,
            "Claude Ack is stale for the live instruction.",
        )
        self.assertEqual(
            state.attention.recommended_action,
            "Reset the implementer state before resuming work.",
        )
        self.assertIn("reset-implementer-state", state.attention.recommended_command)
        self.assertTrue(
            any(
                warning.startswith(
                    "review_state.attention normalized from recovery_assessment projection"
                )
                for warning in state.warnings
            )
        )

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

    def test_optional_review_flags_preserve_unknown_state(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-03-16T02:05:00Z",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "session-optional-flags"},
                    "queue": {"pending_total": 0},
                    "bridge": {
                        "reviewer_mode": "active_dual_agent",
                        "reviewed_hash_current": None,
                        "review_needed": None,
                    },
                    "packets": [],
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertIsNone(state.bridge.reviewed_hash_current)
        self.assertIsNone(state.bridge.review_needed)

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
        self.assertEqual(bridge_state.collaboration.review_agent, "codex")
        self.assertEqual(event_state.collaboration.review_agent, "codex")
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

    def test_review_state_parser_canonicalizes_current_instruction_markdown_revision(
        self,
    ) -> None:
        raw_instruction = "\n".join(
            [
                "Current-instruction authority now converged; stale Claude Status remains",
                "- Context packet: trigger `review-channel-event`; query terms: `bridge.md`, `review_state.json`",
                "- Canonical refs:",
                "  - `dev/active/loop_chat_bridge.md`",
            ]
        )
        raw_revision = sha256(raw_instruction.encode("utf-8")).hexdigest()[:12]

        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-04-13T00:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {
                        "plan_id": "MP-358",
                        "session_id": "markdown-bridge",
                        "surface_mode": "markdown-bridge",
                        "active_lane": "review",
                    },
                    "queue": {"pending_total": 0},
                    "current_session": {
                        "current_instruction": raw_instruction,
                        "current_instruction_revision": raw_revision,
                    },
                    "bridge": {},
                    "packets": [],
                },
                "agent_registry": {
                    "timestamp": "2026-04-13T00:00:00Z",
                    "agents": [],
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertTrue(
            state.current_session.current_instruction.startswith(
                "- Current-instruction authority"
            )
        )
        self.assertEqual(
            state.current_session.current_instruction_revision,
            sha256(
                state.current_session.current_instruction.encode("utf-8")
            ).hexdigest()[:12],
        )


    def test_action_request_packets_project_into_review_state(self) -> None:
        """Action-request packets land in the typed packet list like all other kinds."""
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-04-04T00:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "session-action-req"},
                    "queue": {"pending_total": 1},
                    "bridge": {"reviewer_mode": "active_dual_agent"},
                    "packets": [
                        {
                            "packet_id": "pkt-ar-001",
                            "kind": "action_request",
                            "from_agent": "codex",
                            "to_agent": "claude",
                            "summary": "Commit staged changes",
                            "body": "-m 'fix typo'",
                            "status": "pending",
                            "policy_hint": "safe_auto_apply",
                            "requested_action": "commit",
                            "approval_required": False,
                            "timestamp_utc": "2026-04-04T00:01:00Z",
                        },
                    ],
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(len(state.packets), 1)
        packet = state.packets[0]
        self.assertEqual(packet.kind, "action_request")
        self.assertEqual(packet.requested_action, "commit")
        self.assertEqual(packet.body, "-m 'fix typo'")
        self.assertEqual(packet.status, "pending")

    def test_review_state_promotes_commit_pipeline_push_authorization(self) -> None:
        state = review_state_from_payload(
            {
                "schema_version": 1,
                "command": "review-channel",
                "action": "status",
                "timestamp": "2026-04-05T00:00:00Z",
                "ok": True,
                "review_state": {
                    "review": {"session_id": "session-push-auth"},
                    "queue": {"pending_total": 0},
                    "bridge": {"reviewer_mode": "active_dual_agent"},
                    "commit_pipeline": {
                        "pipeline_id": "pipeline-123",
                        "state": "push_pending",
                        "commit_sha": "abc123",
                        "approved_target_identity": "origin/main@abc123",
                        "push_authorization": {
                            "authorization_id": "push-auth-123",
                            "pipeline_id": "pipeline-123",
                            "generation_id": "gen-123",
                            "authorized_head_sha": "abc123",
                            "approved_target_identity": "origin/main@abc123",
                            "review_verdict": "approved",
                            "approval_mode": "commit_pipeline_approval",
                            "guard_action_id": "quality.guard_bundle",
                            "guard_status": "pass",
                        },
                    },
                },
            }
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertIsNotNone(state.push_authorization)
        assert state.push_authorization is not None
        self.assertEqual(state.push_authorization.authorization_id, "push-auth-123")
        self.assertEqual(
            state.commit_pipeline.push_authorization,
            state.push_authorization,
        )


if __name__ == "__main__":
    unittest.main()
