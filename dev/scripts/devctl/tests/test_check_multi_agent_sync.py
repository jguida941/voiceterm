"""Tests for multi-agent board/runbook synchronization guard."""

import unittest
from unittest.mock import patch

from dev.scripts.checks import check_multi_agent_sync


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

    @patch("dev.scripts.checks.check_multi_agent_sync._extract_table_rows")
    def test_cycle_complete_requires_non_pending_signoff_rows(self, extract_mock) -> None:
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
        self.assertTrue(any("signoff Result must be `pass`" in err for err in report["errors"]))
        self.assertTrue(any("signoff Signature must be populated" in err for err in report["errors"]))

    @patch("dev.scripts.checks.check_multi_agent_sync._extract_table_rows")
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

    @patch("dev.scripts.checks.check_multi_agent_sync._extract_table_rows")
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
        self.assertTrue(any("MP collision requires handoff token" in err for err in report["errors"]))


if __name__ == "__main__":
    unittest.main()
