"""Tests for the portable startup receipt helpers."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.runtime.startup_receipt import (
    StartupReceipt,
    startup_receipt_from_mapping,
    startup_receipt_path,
    startup_receipt_problems,
    startup_receipt_relative_path,
)


class StartupReceiptPathTests(unittest.TestCase):
    def test_receipt_path_uses_governance_reports_root(self) -> None:
        governance = SimpleNamespace(
            path_roots=SimpleNamespace(reports="reports-out")
        )

        relative = startup_receipt_relative_path(governance=governance)

        self.assertEqual(
            relative,
            Path("reports-out") / "startup" / "latest" / "receipt.json",
        )

    def test_receipt_path_falls_back_to_default_reports_root(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = startup_receipt_path(repo_root=Path(tmp_dir))

        self.assertEqual(
            path,
            Path(tmp_dir) / "startup" / "latest" / "receipt.json",
        )

    @patch(
        "dev.scripts.devctl.runtime.startup_receipt.configured_path_config",
        return_value=SimpleNamespace(reports_root_rel="portable-reports"),
    )
    def test_receipt_path_falls_back_to_active_path_config(
        self,
        _configured_path_config,
    ) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = startup_receipt_path(repo_root=Path(tmp_dir))

        self.assertEqual(
            path,
            Path(tmp_dir)
            / "portable-reports"
            / "startup"
            / "latest"
            / "receipt.json",
        )


class StartupReceiptProblemTests(unittest.TestCase):
    def test_receipt_round_trip_preserves_push_decision_fields(self) -> None:
        receipt = startup_receipt_from_mapping(
            {
                "push_action": "run_devctl_push",
                "push_reason": "push_preconditions_satisfied",
                "push_eligible_now": True,
                "push_next_step_summary": "Use the governed push path now.",
                "push_next_step_command": (
                    "python3 dev/scripts/devctl.py push --execute"
                ),
                "publication_backlog_state": "recommended",
                "publication_backlog_summary": (
                    "2 local commit(s) waiting for governed push."
                ),
                "publication_backlog_recommended": True,
                "publication_guidance": (
                    "2 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now."
                ),
            }
        )

        self.assertEqual(receipt.push_action, "run_devctl_push")
        self.assertEqual(receipt.push_reason, "push_preconditions_satisfied")
        self.assertTrue(receipt.push_eligible_now)
        self.assertEqual(
            receipt.push_next_step_command,
            "python3 dev/scripts/devctl.py push --execute",
        )
        self.assertEqual(receipt.publication_backlog_state, "recommended")
        self.assertTrue(receipt.publication_backlog_recommended)

    def test_problem_list_flags_checkpoint_required_receipts(self) -> None:
        receipt = StartupReceipt(
            checkpoint_required=True,
            safe_to_continue_editing=False,
            startup_authority_ok=True,
        )

        with TemporaryDirectory() as tmp_dir:
            problems = startup_receipt_problems(receipt, repo_root=Path(tmp_dir))

        self.assertIn(
            "Latest startup receipt still requires a checkpoint before another implementation or launcher step.",
            problems,
        )


if __name__ == "__main__":
    unittest.main()
