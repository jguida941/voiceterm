"""Tests for multi-agent board/runbook synchronization guard."""

import unittest
from unittest.mock import patch

from dev.scripts.checks.multi_agent_sync import api as check_multi_agent_sync
from dev.scripts.checks.multi_agent_sync.runtime_truth_agent_loop import (
    agent_loop_decision_errors,
)
from dev.scripts.checks.multi_agent_sync.runtime_truth_agent_loop_instruction import (
    instruction_authority_mismatch_errors,
)


def _master_row(agent: str, branch: str, status: str) -> dict:
    return {
        "Agent": agent,
        "Lane": f"{agent} lane",
        "Active-doc scope": "doc",
        "MP scope (authoritative)": "MP-001",
        "Worktree": f"../wt-{agent.lower()}",
        "Branch": branch,
        "Status": status,
        "Last update (UTC)": "2026-02-23T00:00:00Z",
        "Notes": "note",
    }


def _runbook_row(agent: str, branch: str) -> dict:
    return {
        "Agent": agent,
        "Lane": f"{agent} lane",
        "Primary active docs": "doc",
        "MP scope": "MP-001",
        "Worktree": f"../wt-{agent.lower()}",
        "Branch": branch,
    }


def _ledger_row(agent: str, branch: str) -> dict:
    return {
        "UTC": "2026-02-23T00:10:00Z",
        "Actor": agent,
        "Area": agent,
        "Worktree": f"../wt-{agent.lower()}",
        "Branch": branch,
        "Commit": "abc123",
        "MP scope": "MP-001",
        "Verification summary": "checks pass",
        "Status": "merged",
        "Reviewer token": "REVIEW-OK",
        "Next action": "done",
    }


def _instruction_row(agent: str, instruction_id: str, status: str) -> dict:
    return {
        "UTC issued": "2026-02-23T00:00:00Z",
        "Instruction ID": instruction_id,
        "From": "ORCHESTRATOR",
        "To": agent,
        "Summary": "Do lane work",
        "Due (UTC)": "2026-02-23T00:10:00Z",
        "Ack token": "pending" if status == "pending" else f"ACK-{agent}-1",
        "Ack UTC": "pending" if status == "pending" else "2026-02-23T00:05:00Z",
        "Status": status,
    }


def _signoff_row(signer: str, pending: bool) -> dict:
    value = "pending" if pending else "pass"
    return {
        "Signer": signer,
        "Date (UTC)": "pending" if pending else "2026-02-23T09:30:00Z",
        "Result": value,
        "Isolation verified": "pending" if pending else "yes",
        "Bundle reference": "pending" if pending else "bundle://final",
        "Signature": "pending" if pending else f"{signer}-ok",
    }


class CheckMultiAgentSyncTests(unittest.TestCase):
    def test_report_ok_for_current_repo(self) -> None:
        report = check_multi_agent_sync._build_report()
        self.assertTrue(report["ok"], report.get("errors"))

    @patch("dev.scripts.checks.multi_agent_sync.api._extract_table_rows")
    def test_cycle_complete_requires_non_pending_signoff_rows(
        self, extract_mock
    ) -> None:
        master_rows = [
            _master_row("AGENT-1", "feature/a1-runtime-theme", "merged"),
            _master_row("AGENT-2", "feature/a2-tooling-control-plane", "merged"),
            _master_row("AGENT-3", "feature/a3-memory-mutation-reliability", "merged"),
        ]
        runbook_rows = [
            _runbook_row("AGENT-1", "feature/a1-runtime-theme"),
            _runbook_row("AGENT-2", "feature/a2-tooling-control-plane"),
            _runbook_row("AGENT-3", "feature/a3-memory-mutation-reliability"),
        ]
        ledger_rows = [
            _ledger_row("AGENT-1", "feature/a1-runtime-theme"),
            _ledger_row("AGENT-2", "feature/a2-tooling-control-plane"),
            _ledger_row("AGENT-3", "feature/a3-memory-mutation-reliability"),
        ]
        instruction_rows = [
            _instruction_row("AGENT-1", "INS-1", "completed"),
            _instruction_row("AGENT-2", "INS-2", "completed"),
            _instruction_row("AGENT-3", "INS-3", "completed"),
        ]
        signoff_rows = [
            _signoff_row("AGENT-1", pending=True),
            _signoff_row("AGENT-2", pending=True),
            _signoff_row("AGENT-3", pending=True),
            _signoff_row("ORCHESTRATOR", pending=True),
        ]
        extract_mock.side_effect = [
            (master_rows, None),
            (runbook_rows, None),
            (instruction_rows, None),
            (ledger_rows, None),
            (signoff_rows, None),
        ]

        report = check_multi_agent_sync._build_report()
        self.assertFalse(report["ok"])
        self.assertTrue(
            any("signoff Result must be `pass`" in err for err in report["errors"])
        )
        self.assertTrue(
            any(
                "signoff Signature must be populated" in err for err in report["errors"]
            )
        )

    @patch("dev.scripts.checks.multi_agent_sync.api._extract_table_rows")
    def test_dynamic_agent_count_is_supported(self, extract_mock) -> None:
        agents = ("AGENT-1", "AGENT-2", "AGENT-3", "AGENT-4")
        master_rows = []
        runbook_rows = []
        for idx, agent in enumerate(agents):
            scope = f"MP-{101 + idx:03d}"
            master_row = _master_row(agent, f"feature/{agent.lower()}", "planned")
            master_row["MP scope (authoritative)"] = scope
            runbook_row = _runbook_row(agent, f"feature/{agent.lower()}")
            runbook_row["MP scope"] = scope
            master_rows.append(master_row)
            runbook_rows.append(runbook_row)
        instruction_rows = [
            _instruction_row(agent, f"INS-{idx + 1}", "completed")
            for idx, agent in enumerate(agents)
        ]
        signoff_rows = [_signoff_row(agent, pending=True) for agent in agents] + [
            _signoff_row("ORCHESTRATOR", pending=True)
        ]
        extract_mock.side_effect = [
            (master_rows, None),
            (runbook_rows, None),
            (instruction_rows, None),
            ([], None),
            (signoff_rows, None),
        ]

        report = check_multi_agent_sync._build_report()

        self.assertTrue(report["ok"], report.get("errors"))
        self.assertEqual(report["required_agents"], list(agents))

    @patch("dev.scripts.checks.multi_agent_sync.api._extract_table_rows")
    def test_mp_scope_overlap_requires_handoff_token(self, extract_mock) -> None:
        master_rows = [
            _master_row("AGENT-1", "feature/a1-runtime-theme", "planned"),
            _master_row("AGENT-2", "feature/a2-tooling-control-plane", "planned"),
            _master_row("AGENT-3", "feature/a3-memory-mutation-reliability", "planned"),
        ]
        master_rows[0]["MP scope (authoritative)"] = "MP-001, MP-002"
        master_rows[1]["MP scope (authoritative)"] = "MP-002, MP-010"
        runbook_rows = [
            _runbook_row("AGENT-1", "feature/a1-runtime-theme"),
            _runbook_row("AGENT-2", "feature/a2-tooling-control-plane"),
            _runbook_row("AGENT-3", "feature/a3-memory-mutation-reliability"),
        ]
        instruction_rows = [
            _instruction_row("AGENT-1", "INS-1", "completed"),
            _instruction_row("AGENT-2", "INS-2", "completed"),
            _instruction_row("AGENT-3", "INS-3", "completed"),
        ]
        signoff_rows = [
            _signoff_row("AGENT-1", pending=True),
            _signoff_row("AGENT-2", pending=True),
            _signoff_row("AGENT-3", pending=True),
            _signoff_row("ORCHESTRATOR", pending=True),
        ]
        extract_mock.side_effect = [
            (master_rows, None),
            (runbook_rows, None),
            (instruction_rows, None),
            ([], None),
            (signoff_rows, None),
        ]

        report = check_multi_agent_sync._build_report()
        self.assertFalse(report["ok"])
        self.assertTrue(
            any(
                "MP collision requires handoff token" in err for err in report["errors"]
            )
        )

    def test_attention_packet_is_not_treated_as_current_instruction(self) -> None:
        payload = {
            "queue": {
                "derived_next_instruction_source": {
                    "to_agent": "claude",
                    "packet_id": "rev_pkt_2546",
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
        }
        decisions = [
            {
                "actor_id": "claude",
                "active_packet_id": "",
                "attention_packet_id": "rev_pkt_2563",
            }
        ]

        self.assertEqual(instruction_authority_mismatch_errors(payload, decisions), [])

    def test_legacy_unscoped_packet_conserves_work_board_focus(self) -> None:
        payload = {
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "claude",
                        "role": "dashboard",
                        "session_id": "s-1",
                        "active_packet_id": "rev_pkt_2288",
                        "attention_packet_id": "rev_pkt_2288",
                    }
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "claude",
                    "actor_role": "dashboard",
                    "session_id": "s-1",
                    "active_packet_id": "",
                    "attention_packet_id": "",
                    "legacy_unscoped_packet_id": "rev_pkt_2288",
                }
            ],
        }

        self.assertEqual(agent_loop_decision_errors(payload), [])

    def test_wrong_legacy_unscoped_packet_still_fails_focus_check(self) -> None:
        payload = {
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "claude",
                        "role": "dashboard",
                        "session_id": "s-1",
                        "active_packet_id": "rev_pkt_2288",
                        "attention_packet_id": "rev_pkt_2288",
                    }
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "claude",
                    "actor_role": "dashboard",
                    "session_id": "s-1",
                    "active_packet_id": "",
                    "attention_packet_id": "",
                    "legacy_unscoped_packet_id": "rev_pkt_other",
                }
            ],
        }

        errors = agent_loop_decision_errors(payload)

        self.assertEqual(len(errors), 2)
        self.assertTrue(any("active packet does not match" in err for err in errors))

    def test_active_packet_still_must_match_current_instruction(self) -> None:
        payload = {
            "queue": {
                "derived_next_instruction_source": {
                    "to_agent": "claude",
                    "packet_id": "rev_pkt_2546",
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
        }
        decisions = [
            {
                "actor_id": "claude",
                "active_packet_id": "rev_pkt_2563",
                "attention_packet_id": "rev_pkt_2563",
            }
        ]

        errors = instruction_authority_mismatch_errors(payload, decisions)

        self.assertEqual(len(errors), 2)
        self.assertTrue(
            any("Queue-derived current instruction disagrees" in err for err in errors)
        )
        self.assertTrue(
            any("Packet inbox current instruction disagrees" in err for err in errors)
        )

    def test_communication_only_packet_is_not_instruction_authority(self) -> None:
        payload = {
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "codex",
                        "current_instruction_packet_id": "rev_pkt_review_accept",
                    }
                ]
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_review_accept",
                    "kind": "review_accepted",
                    "to_agent": "codex",
                    "durable_binding": {
                        "binding_target_kind": "communication_only",
                    },
                }
            ],
        }
        decisions = [
            {
                "actor_id": "codex",
                "active_packet_id": "rev_pkt_finding",
                "attention_packet_id": "rev_pkt_finding",
            }
        ]

        self.assertEqual(instruction_authority_mismatch_errors(payload, decisions), [])

    def test_executing_packet_can_coexist_with_next_instruction_packet(self) -> None:
        payload = {
            "queue": {
                "derived_next_instruction_source": {
                    "to_agent": "claude",
                    "packet_id": "rev_pkt_next",
                    "target_role": "implementer",
                    "target_session_id": "session-live",
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
                    "target_session_id": "session-live",
                }
            ],
        }
        decisions = [
            {
                "actor_id": "claude",
                "actor_role": "implementer",
                "session_id": "session-live",
                "active_packet_id": "rev_pkt_executing",
                "attention_packet_id": "rev_pkt_executing",
                "executing_packet_id": "rev_pkt_executing",
                "pending_packet_count": 1,
            }
        ]

        self.assertEqual(instruction_authority_mismatch_errors(payload, decisions), [])

    def test_same_session_execution_can_cross_legacy_role_label(self) -> None:
        payload = {
            "queue": {
                "derived_next_instruction_source": {
                    "to_agent": "claude",
                    "packet_id": "rev_pkt_next",
                    "target_role": "implementer",
                    "target_session_id": "session-live",
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
                    "target_session_id": "session-live",
                }
            ],
        }
        decisions = [
            {
                "actor_id": "claude",
                "actor_role": "reviewer",
                "session_id": "session-live",
                "active_packet_id": "rev_pkt_executing",
                "attention_packet_id": "rev_pkt_executing",
                "executing_packet_id": "rev_pkt_executing",
                "pending_packet_count": 1,
            },
            {
                "actor_id": "claude",
                "actor_role": "implementer",
                "session_id": "session-live",
                "active_packet_id": "rev_pkt_executing",
                "attention_packet_id": "rev_pkt_executing",
                "executing_packet_id": "",
                "pending_packet_count": 1,
            },
        ]

        self.assertEqual(instruction_authority_mismatch_errors(payload, decisions), [])

    def test_scoped_dashboard_instruction_ignores_subagent_active_packet(self) -> None:
        payload = {
            "queue": {
                "derived_next_instruction_source": {
                    "to_agent": "claude",
                    "packet_id": "rev_pkt_3100",
                    "target_role": "dashboard",
                    "target_session_id": "session-a",
                }
            },
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "current_instruction_packet_id": "rev_pkt_3100",
                    }
                ]
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_3100",
                    "to_agent": "claude",
                    "target_role": "dashboard",
                    "target_session_id": "session-a",
                }
            ],
        }
        decisions = [
            {
                "actor_id": "claude",
                "actor_role": "subagent",
                "session_id": "session-a",
                "active_packet_id": "rev_pkt_2980",
                "attention_packet_id": "rev_pkt_2980",
            }
        ]

        self.assertEqual(instruction_authority_mismatch_errors(payload, decisions), [])

    def test_scoped_dashboard_instruction_still_blocks_same_scope_drift(self) -> None:
        payload = {
            "queue": {
                "derived_next_instruction_source": {
                    "to_agent": "claude",
                    "packet_id": "rev_pkt_3100",
                    "target_role": "dashboard",
                    "target_session_id": "session-a",
                }
            },
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "current_instruction_packet_id": "rev_pkt_3100",
                    }
                ]
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_3100",
                    "to_agent": "claude",
                    "target_role": "dashboard",
                    "target_session_id": "session-a",
                }
            ],
        }
        decisions = [
            {
                "actor_id": "claude",
                "actor_role": "dashboard",
                "session_id": "session-a",
                "active_packet_id": "rev_pkt_2980",
                "attention_packet_id": "rev_pkt_2980",
            }
        ]

        errors = instruction_authority_mismatch_errors(payload, decisions)

        self.assertEqual(len(errors), 2)
        self.assertTrue(
            any("Queue-derived current instruction disagrees" in err for err in errors)
        )
        self.assertTrue(
            any("Packet inbox current instruction disagrees" in err for err in errors)
        )


if __name__ == "__main__":
    unittest.main()
