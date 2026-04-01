"""Runtime-truth coverage for the multi-agent sync guard wrapper."""

import unittest
from unittest.mock import patch

from dev.scripts.checks.multi_agent_sync import api as check_multi_agent_sync
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
            "errors": [
                "Planned AGENT rows leaked into runtime registry without live worker receipts: AGENT-1"
            ],
        }

        report = check_multi_agent_sync._build_report()

        self.assertFalse(report["ok"])
        self.assertTrue(report["runtime_truth_checked"])
        self.assertEqual(
            report["runtime_review_state_path"],
            "dev/reports/review_channel/latest/review_state.json",
        )
        self.assertTrue(
            any(
                "Planned AGENT rows leaked into runtime registry"
                in err
                for err in report["errors"]
            )
        )


if __name__ == "__main__":
    unittest.main()
