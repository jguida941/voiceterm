"""Runtime-truth coverage for the multi-agent sync guard wrapper."""

import unittest
from unittest.mock import patch
from pathlib import Path

from dev.scripts.checks.multi_agent_sync import api as check_multi_agent_sync
from dev.scripts.checks.multi_agent_sync import runtime_truth
from dev.scripts.checks.multi_agent_sync.report import render_md
from dev.scripts.devctl.tests.checks.test_check_multi_agent_sync import (
    _instruction_row,
    _master_row,
    _runbook_row,
    _signoff_row,
)


class CheckMultiAgentSyncRuntimeTruthTests(unittest.TestCase):
    @patch("dev.scripts.checks.multi_agent_sync.api.evaluate_runtime_truth")
    @patch("dev.scripts.checks.multi_agent_sync.api._extract_table_rows")
    def test_runtime_truth_errors_are_blocking(
        self,
        extract_mock,
        runtime_truth_mock,
    ) -> None:
        master_rows = [_master_row("AGENT-1", "feature/a1", "planned")]
        runbook_rows = [_runbook_row("AGENT-1", "feature/a1")]
        instruction_rows = [_instruction_row("AGENT-1", "INS-1", "completed")]
        signoff_rows = [
            _signoff_row("AGENT-1", pending=True),
            _signoff_row("ORCHESTRATOR", pending=True),
        ]
        extract_mock.side_effect = [
            (master_rows, None),
            (runbook_rows, None),
            (instruction_rows, None),
            ([], None),
            (signoff_rows, None),
        ]
        runtime_truth_mock.return_value = {
            "checked": True,
            "review_state_path": "dev/reports/review_channel/latest/review_state.json",
            "coordination_topology": "multi_agent_active",
            "legacy_reviewer_mode": "single_agent",
            "active_runtime_providers": ["codex", "claude"],
            "agent_work_board_row_count": 2,
            "agent_loop_decision_row_count": 2,
            "pending_packet_agents": ["claude"],
            "warnings": [
                "Typed coordination topology differs from legacy reviewer mode: "
                "coordination_topology=multi_agent_active; "
                "legacy_reviewer_mode=single_agent. "
                "Use coordination_topology for runtime topology."
            ],
            "errors": [
                "Planned AGENT rows leaked into runtime registry without "
                "live worker receipts: AGENT-1"
            ],
        }

        report = check_multi_agent_sync._build_report()

        self.assertFalse(report["ok"])
        self.assertTrue(report["runtime_truth_checked"])
        self.assertEqual(
            report["runtime_review_state_path"],
            "dev/reports/review_channel/latest/review_state.json",
        )
        self.assertEqual(report["runtime_coordination_topology"], "multi_agent_active")
        self.assertEqual(report["runtime_legacy_reviewer_mode"], "single_agent")
        self.assertEqual(report["runtime_active_runtime_providers"], ["codex", "claude"])
        self.assertEqual(report["runtime_agent_work_board_rows"], 2)
        self.assertEqual(report["runtime_agent_loop_decisions"], 2)
        self.assertEqual(report["runtime_pending_packet_agents"], ["claude"])
        self.assertTrue(
            any("Typed coordination topology differs" in item for item in report["warnings"])
        )
        output = render_md(report)
        self.assertIn("- runtime_coordination_topology: multi_agent_active", output)
        self.assertIn("- runtime_agent_loop_decisions: 2", output)
        self.assertIn("- runtime_pending_packet_agents: claude", output)
        self.assertTrue(
            any(
                "Planned AGENT rows leaked into runtime registry"
                in err
                for err in report["errors"]
            )
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_reports_typed_topology_mismatch(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [{"gate_id": "delegated_work", "status": "not_requested"}],
            },
            "registry": {"agents": []},
            "coordination_state": {
                "coordination_topology": "multi_agent_active",
                "legacy_reviewer_mode": "single_agent",
                "observed_runtime": {
                    "active_runtime_providers": ["codex", "claude"],
                },
            },
            "agent_sync": {
                "agents": {
                    "claude": {
                        "pending_packets_to_me": ["rev_pkt_1"],
                    },
                    "codex": {
                        "pending_packets_to_me": [],
                    },
                }
            },
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "claude",
                        "role": "implementer",
                        "session_id": "s-claude",
                        "active_packet_id": "rev_pkt_1",
                        "attention_packet_id": "rev_pkt_1",
                    }
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "claude",
                    "actor_role": "implementer",
                    "session_id": "s-claude",
                    "active_packet_id": "rev_pkt_1",
                    "attention_packet_id": "rev_pkt_1",
                    "pending_packet_count": 1,
                }
            ],
            "reviewer_runtime": {
                "packet_attention": {
                    "observation_actor_id": "",
                    "pending_packet_count": 1,
                    "wake_required": True,
                    "stale_reason": "actor_identity_ambiguous_with_pending_wake",
                }
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertEqual(result["coordination_topology"], "multi_agent_active")
        self.assertEqual(result["legacy_reviewer_mode"], "single_agent")
        self.assertEqual(result["active_runtime_providers"], ["codex", "claude"])
        self.assertEqual(result["agent_work_board_row_count"], 1)
        self.assertEqual(result["agent_loop_decision_row_count"], 1)
        self.assertEqual(result["pending_packet_agents"], ["claude"])
        self.assertTrue(
            any("Typed coordination topology differs" in item for item in result["warnings"])
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_blocks_agent_loop_output_drift(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "agent_sync": {
                "agents": {
                    "claude": {
                        "pending_packets_to_me": ["rev_pkt_1"],
                    }
                }
            },
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "claude",
                        "role": "implementer",
                        "session_id": "s-claude",
                        "active_packet_id": "rev_pkt_1",
                        "attention_packet_id": "rev_pkt_1",
                    }
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "claude",
                    "actor_role": "implementer",
                    "session_id": "s-claude",
                    "active_packet_id": "",
                    "attention_packet_id": "",
                    "pending_packet_count": 0,
                }
            ],
            "reviewer_runtime": {
                "packet_attention": {
                    "observation_actor_id": "",
                    "pending_packet_count": 0,
                    "wake_required": False,
                    "stale_reason": "actor_identity_ambiguous",
                }
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertTrue(
            any("active packet does not match" in err for err in result["errors"])
        )
        self.assertTrue(
            any("attention packet does not match" in err for err in result["errors"])
        )
        self.assertTrue(
            any("no pending count for: claude" in err for err in result["errors"])
        )
        self.assertTrue(
            any("wake_required=false" in err for err in result["errors"])
        )
        self.assertTrue(
            any("pending_packet_count=0" in err for err in result["errors"])
        )
        self.assertTrue(
            any(
                "actor_identity_ambiguous_with_pending_wake" in err
                for err in result["errors"]
            )
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_allows_stale_read_only_board_rows_without_loop_decisions(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "agent_sync": {"agents": {}},
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "claude",
                        "role": "dashboard",
                        "session_id": "s-stale",
                        "idle_seconds": 1200,
                        "stale_after_seconds": 600,
                        "confidence_class": "stale",
                        "active_packet_id": "",
                        "attention_packet_id": "",
                        "executing_packet_id": "",
                    },
                    {
                        "actor_id": "codex",
                        "role": "dashboard",
                        "session_id": "s-live",
                        "idle_seconds": 10,
                        "stale_after_seconds": 600,
                        "confidence_class": "derived_typed_event",
                    },
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "codex",
                    "actor_role": "dashboard",
                    "session_id": "s-live",
                    "pending_packet_count": 0,
                }
            ],
            "reviewer_runtime": {
                "packet_attention": {
                    "observation_actor_id": "",
                    "pending_packet_count": 0,
                    "wake_required": False,
                    "stale_reason": "",
                }
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertFalse(
            any("s-stale" in err for err in result["errors"])
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_allows_operator_read_only_notice_without_loop_wake(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "agent_sync": {
                "agents": {
                    "operator": {
                        "pending_packets_to_me": ["rev_pkt_notice"],
                    },
                }
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_notice",
                    "to_agent": "operator",
                    "kind": "system_notice",
                    "requested_action": "review_only",
                    "policy_hint": "review_only",
                    "approval_required": False,
                    "status": "pending",
                    "lifecycle_current_state": "pending",
                }
            ],
            "agent_work_board": {"rows": []},
            "agent_loop_decisions": [],
            "reviewer_runtime": {
                "packet_attention": {
                    "observation_actor_id": "",
                    "pending_packet_count": 0,
                    "wake_required": False,
                    "stale_reason": "",
                }
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertEqual(result["pending_packet_agents"], [])
        self.assertFalse(
            any("no pending count for: operator" in err for err in result["errors"])
        )
        self.assertFalse(
            any("actor_identity_ambiguous_with_pending_wake" in err for err in result["errors"])
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_repairs_missing_pending_actor_projection_from_agent_sync(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "current_session": {"current_instruction_revision": ""},
            "reviewer_runtime": {
                "agent_runtime_clock": {"source_latest_event_id": "rev_evt_2"},
                "packet_attention": {
                    "observation_actor_id": "",
                    "pending_packet_count": 0,
                    "wake_required": False,
                    "stale_reason": "actor_identity_ambiguous",
                },
            },
            "agent_sync": {
                "agents": {
                    "claude": {
                        "pending_packets_to_me": ["rev_pkt_finding"],
                        "last_consumed_event_id_lower_bound": "rev_evt_1",
                    }
                }
            },
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "codex",
                        "role": "reviewer",
                        "session_id": "s-codex",
                        "idle_seconds": 10,
                        "stale_after_seconds": 600,
                    }
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "codex",
                    "actor_role": "reviewer",
                    "session_id": "s-codex",
                    "pending_packet_count": 0,
                }
            ],
            "packets": [
                {
                    "packet_id": "rev_pkt_finding",
                    "to_agent": "claude",
                    "kind": "finding",
                    "status": "pending",
                    "lifecycle_current_state": "pending",
                    "latest_event_id": "rev_evt_2",
                    "requested_action": "review_only",
                    "policy_hint": "review_only",
                    "approval_required": False,
                    "expires_at_utc": "2999-01-01T00:00:00Z",
                }
            ],
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertEqual(result["pending_packet_agents"], ["claude"])
        self.assertFalse(
            any("no pending count for: claude" in err for err in result["errors"])
        )
        self.assertFalse(
            any("wake_required=false" in err for err in result["errors"])
        )
        self.assertFalse(
            any("pending_packet_count=0" in err for err in result["errors"])
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_blocks_queue_and_inbox_instruction_drift(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "queue": {
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_2546",
                    "to_agent": "claude",
                }
            },
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "current_instruction_packet_id": "rev_pkt_2546",
                    }
                ]
            },
            "agent_sync": {"agents": {}},
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "claude",
                        "role": "implementer",
                        "session_id": "s-claude",
                        "active_packet_id": "rev_pkt_2547",
                        "attention_packet_id": "rev_pkt_2547",
                    }
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "claude",
                    "actor_role": "implementer",
                    "session_id": "s-claude",
                    "active_packet_id": "rev_pkt_2547",
                    "attention_packet_id": "rev_pkt_2547",
                    "pending_packet_count": 1,
                }
            ],
            "reviewer_runtime": {
                "packet_attention": {
                    "observation_actor_id": "",
                    "pending_packet_count": 1,
                    "wake_required": True,
                    "stale_reason": "actor_identity_ambiguous_with_pending_wake",
                }
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertTrue(
            any("Queue-derived current instruction disagrees" in err for err in result["errors"])
        )
        self.assertTrue(
            any("Packet inbox current instruction disagrees" in err for err in result["errors"])
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_allows_session_scoped_instruction_authority(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "queue": {
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_new",
                    "to_agent": "claude",
                    "target_role": "implementer",
                    "target_session_id": "s-new",
                }
            },
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "current_instruction_packet_id": "rev_pkt_new",
                    }
                ]
            },
            "agent_sync": {
                "agents": {
                    "claude": {
                        "pending_packets_to_me": ["rev_pkt_new", "rev_pkt_old"],
                    }
                }
            },
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "claude",
                        "role": "implementer",
                        "session_id": "s-old",
                        "active_packet_id": "rev_pkt_old",
                        "attention_packet_id": "rev_pkt_old",
                    },
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "claude",
                    "actor_role": "implementer",
                    "session_id": "s-old",
                    "active_packet_id": "rev_pkt_old",
                    "attention_packet_id": "rev_pkt_old",
                    "pending_packet_count": 1,
                },
                {
                    "actor_id": "claude",
                    "actor_role": "implementer",
                    "session_id": "s-new",
                    "active_packet_id": "rev_pkt_new",
                    "attention_packet_id": "rev_pkt_new",
                    "pending_packet_count": 1,
                    "source_work_board_row": {
                        "status": "queue_targeted",
                        "confidence_class": "queue_scoped_packet",
                    },
                },
            ],
            "reviewer_runtime": {
                "packet_attention": {
                    "observation_actor_id": "",
                    "pending_packet_count": 2,
                    "wake_required": True,
                    "stale_reason": "actor_identity_ambiguous_with_pending_wake",
                }
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertFalse(
            any("current instruction disagrees" in err for err in result["errors"])
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_allows_executing_packet_with_pending_next_instruction(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "queue": {
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_next",
                    "to_agent": "claude",
                    "target_role": "implementer",
                    "target_session_id": "s-claude",
                }
            },
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "current_instruction_packet_id": "rev_pkt_next",
                    }
                ]
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_next",
                    "to_agent": "claude",
                    "target_role": "implementer",
                    "target_session_id": "s-claude",
                }
            ],
            "agent_sync": {
                "agents": {
                    "claude": {
                        "pending_packets_to_me": ["rev_pkt_next"],
                    }
                }
            },
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "claude",
                        "role": "implementer",
                        "session_id": "s-claude",
                        "active_packet_id": "rev_pkt_executing",
                        "attention_packet_id": "rev_pkt_executing",
                        "executing_packet_id": "rev_pkt_executing",
                    }
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "claude",
                    "actor_role": "implementer",
                    "session_id": "s-claude",
                    "active_packet_id": "rev_pkt_executing",
                    "attention_packet_id": "rev_pkt_executing",
                    "executing_packet_id": "rev_pkt_executing",
                    "pending_packet_count": 1,
                }
            ],
            "reviewer_runtime": {
                "packet_attention": {
                    "observation_actor_id": "",
                    "pending_packet_count": 1,
                    "wake_required": True,
                    "stale_reason": "actor_identity_ambiguous_with_pending_wake",
                }
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertFalse(
            any("current instruction disagrees" in err for err in result["errors"])
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_allows_same_session_execution_across_role_label(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "queue": {
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_next",
                    "to_agent": "claude",
                    "target_role": "implementer",
                    "target_session_id": "s-claude",
                }
            },
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "current_instruction_packet_id": "rev_pkt_next",
                    }
                ]
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_next",
                    "to_agent": "claude",
                    "target_role": "implementer",
                    "target_session_id": "s-claude",
                }
            ],
            "agent_sync": {"agents": {}},
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "claude",
                        "role": "reviewer",
                        "session_id": "s-claude",
                        "active_packet_id": "rev_pkt_executing",
                        "attention_packet_id": "rev_pkt_executing",
                        "executing_packet_id": "rev_pkt_executing",
                    },
                    {
                        "actor_id": "claude",
                        "role": "implementer",
                        "session_id": "s-claude",
                        "active_packet_id": "rev_pkt_executing",
                        "attention_packet_id": "rev_pkt_executing",
                        "executing_packet_id": "",
                    },
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "claude",
                    "actor_role": "reviewer",
                    "session_id": "s-claude",
                    "active_packet_id": "rev_pkt_executing",
                    "attention_packet_id": "rev_pkt_executing",
                    "executing_packet_id": "rev_pkt_executing",
                    "pending_packet_count": 1,
                },
                {
                    "actor_id": "claude",
                    "actor_role": "implementer",
                    "session_id": "s-claude",
                    "active_packet_id": "rev_pkt_executing",
                    "attention_packet_id": "rev_pkt_executing",
                    "executing_packet_id": "",
                    "pending_packet_count": 1,
                },
            ],
            "reviewer_runtime": {
                "packet_attention": {
                    "observation_actor_id": "",
                    "pending_packet_count": 1,
                    "wake_required": True,
                    "stale_reason": "actor_identity_ambiguous_with_pending_wake",
                }
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertFalse(
            any("current instruction disagrees" in err for err in result["errors"])
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_blocks_unscoped_agent_sync_attention_when_sessions_disagree(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "agent_sync": {
                "agents": {
                    "claude": {
                        "attention_packet_id": "rev_pkt_old",
                        "pending_packets_to_me": ["rev_pkt_old"],
                    }
                }
            },
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "claude",
                        "role": "implementer",
                        "session_id": "s-old",
                        "active_packet_id": "rev_pkt_old",
                        "attention_packet_id": "rev_pkt_old",
                    },
                    {
                        "actor_id": "claude",
                        "role": "implementer",
                        "session_id": "s-new",
                        "active_packet_id": "rev_pkt_new",
                        "attention_packet_id": "rev_pkt_new",
                    },
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "claude",
                    "actor_role": "implementer",
                    "session_id": "s-old",
                    "active_packet_id": "rev_pkt_old",
                    "attention_packet_id": "rev_pkt_old",
                    "pending_packet_count": 1,
                },
                {
                    "actor_id": "claude",
                    "actor_role": "implementer",
                    "session_id": "s-new",
                    "active_packet_id": "rev_pkt_new",
                    "attention_packet_id": "rev_pkt_new",
                    "pending_packet_count": 1,
                },
            ],
            "reviewer_runtime": {
                "packet_attention": {
                    "observation_actor_id": "",
                    "pending_packet_count": 2,
                    "wake_required": True,
                    "stale_reason": "actor_identity_ambiguous_with_pending_wake",
                }
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertTrue(
            any(
                "Agent sync exposes an unscoped attention packet" in err
                for err in result["errors"]
            )
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_blocks_overlapping_live_write_scope_without_lease_or_plan(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "agent_work_board": {
                "rows": [
                    _runtime_work_row(
                        session_id="codex-a",
                        current_file_or_module=(
                            "dev/scripts/devctl/runtime/agent_dispatch_router.py"
                        ),
                    ),
                    _runtime_work_row(
                        session_id="codex-b",
                        current_file_or_module=(
                            "dev/scripts/devctl/runtime/agent_dispatch_router.py"
                        ),
                    ),
                ]
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertTrue(
            any(
                "overlapping_write_scope_without_lease_or_plan" in err
                for err in result["errors"]
            )
        )

    @patch(
        "dev.scripts.checks.multi_agent_sync.runtime_truth."
        "resolved_review_state_relative_path"
    )
    @patch("dev.scripts.checks.multi_agent_sync.runtime_truth.load_review_state_payload")
    def test_runtime_truth_allows_overlapping_scope_with_shared_plan_binding(
        self,
        load_payload_mock,
        relpath_mock,
    ) -> None:
        relpath_mock.return_value = "dev/reports/review_channel/latest/review_state.json"
        load_payload_mock.return_value = {
            "collaboration": {
                "participants": [],
                "delegated_work": [],
                "ready_gates": [],
            },
            "registry": {"agents": []},
            "agent_work_board": {
                "rows": [
                    _runtime_work_row(
                        session_id="codex-a",
                        current_file_or_module=(
                            "dev/scripts/devctl/runtime/agent_dispatch_router.py"
                        ),
                        plan_row_id="MP377-P0-T22AF-E",
                    ),
                    _runtime_work_row(
                        session_id="codex-b",
                        current_file_or_module=(
                            "dev/scripts/devctl/runtime/agent_dispatch_router.py"
                        ),
                        plan_row_id="MP377-P0-T22AF-E",
                    ),
                ]
            },
        }

        result = runtime_truth.evaluate_runtime_truth(
            repo_root=Path("/repo"),
            planned_agent_ids=[],
        )

        self.assertTrue(result["checked"])
        self.assertFalse(
            any(
                "overlapping_write_scope_without_lease_or_plan" in err
                for err in result["errors"]
            )
        )


def _runtime_work_row(
    *,
    session_id: str,
    current_file_or_module: str,
    plan_row_id: str = "",
) -> dict[str, object]:
    return {
        "actor_id": "codex",
        "provider": "codex",
        "role": "reviewer",
        "session_id": session_id,
        "worktree_identity": "../wt",
        "path_scope": ["dev/scripts/devctl/runtime"],
        "current_file_or_module": current_file_or_module,
        "mutation_mode": "live_tree",
        "plan_row_id": plan_row_id,
        "status": "polling",
        "idle_seconds": 1,
        "stale_after_seconds": 600,
        "confidence_class": "derived_typed_event",
        "source_event_id": f"rev_evt_{session_id}",
    }


if __name__ == "__main__":
    unittest.main()
