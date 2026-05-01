"""Tests for the portable startup receipt helpers."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.runtime.startup_receipt import (
    REVIEWER_BOOTSTRAP_STARTUP_INTENT,
    StartupReceipt,
    startup_receipt_from_mapping,
    startup_receipt_path,
    startup_receipt_problems,
    startup_receipt_problems_for_intent,
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
                "staged_path_count": 4,
                "unstaged_path_count": 1,
                "publication_guidance": (
                    "2 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now."
                ),
                "authority_snapshot": {
                    "coordination_state": "handshake_stale",
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "stale",
                    "next_command": "python3 dev/scripts/devctl.py commit -m \"checkpoint\"",
                    "safe_to_continue": False,
                },
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
        self.assertEqual(receipt.staged_path_count, 4)
        self.assertEqual(receipt.unstaged_path_count, 1)
        self.assertIsNotNone(receipt.authority_snapshot)
        assert receipt.authority_snapshot is not None
        self.assertEqual(
            receipt.authority_snapshot.current_instruction_revision,
            "rev123",
        )
        self.assertEqual(receipt.authority_snapshot.implementer_ack_state, "stale")

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

    def test_problem_list_flags_live_startup_authority_drift(self) -> None:
        receipt = StartupReceipt(
            checkpoint_required=False,
            safe_to_continue_editing=True,
            startup_authority_ok=True,
            staged_path_count=0,
            unstaged_path_count=0,
        )

        with TemporaryDirectory() as tmp_dir:
            problems = startup_receipt_problems_for_intent(
                receipt,
                repo_root=Path(tmp_dir),
                authority_report={
                    "ok": False,
                    "checkpoint_required": True,
                    "safe_to_continue_editing": False,
                    "checkpoint_reason": "staged_index_budget_exceeded",
                    "staged_path_count": 5,
                    "unstaged_path_count": 1,
                },
            )

        self.assertTrue(
            any("current startup-authority state" in problem for problem in problems)
        )

    @patch(
        "dev.scripts.devctl.runtime.startup_receipt_freshness._quality_scope_changed_paths",
        return_value=(),
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_receipt_freshness._changed_paths_since",
        return_value=(Path("dev/reports/review_channel/latest/review_state.json"),),
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_receipt_freshness._git_stdout",
        side_effect=("feature/test", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
    )
    def test_bootstrap_problem_allows_admin_only_head_drift(
        self,
        _git_stdout,
        _changed_paths_since,
        _quality_scope_changed_paths,
    ) -> None:
        receipt = StartupReceipt(
            current_branch="feature/test",
            head_commit_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            startup_authority_ok=False,
            reviewer_loop_blocked=True,
            receipt_admin_drift_allowed=True,
        )

        with TemporaryDirectory() as tmp_dir:
            problems = startup_receipt_problems_for_intent(
                receipt,
                repo_root=Path(tmp_dir),
                intent=REVIEWER_BOOTSTRAP_STARTUP_INTENT,
            )

        self.assertEqual(problems, [])

    @patch(
        "dev.scripts.devctl.runtime.startup_receipt_freshness._quality_scope_changed_paths",
        return_value=(Path("dev/scripts/devctl/runtime/startup_gate.py"),),
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_receipt_freshness._changed_paths_since",
        return_value=(Path("dev/scripts/devctl/runtime/startup_gate.py"),),
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_receipt_freshness._git_stdout",
        side_effect=("feature/test", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
    )
    def test_bootstrap_problem_blocks_quality_scope_head_drift(
        self,
        _git_stdout,
        _changed_paths_since,
        _quality_scope_changed_paths,
    ) -> None:
        receipt = StartupReceipt(
            current_branch="feature/test",
            head_commit_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            startup_authority_ok=False,
        )

        with TemporaryDirectory() as tmp_dir:
            problems = startup_receipt_problems_for_intent(
                receipt,
                repo_root=Path(tmp_dir),
                intent=REVIEWER_BOOTSTRAP_STARTUP_INTENT,
            )

        self.assertEqual(len(problems), 1)
        self.assertIn("quality-scope files", problems[0])

    @patch(
        "dev.scripts.devctl.runtime.startup_receipt_freshness._git_stdout",
        side_effect=("feature/other", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
    )
    def test_bootstrap_problem_still_blocks_branch_switch(
        self,
        _git_stdout,
    ) -> None:
        receipt = StartupReceipt(
            current_branch="feature/test",
            head_commit_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )

        with TemporaryDirectory() as tmp_dir:
            problems = startup_receipt_problems_for_intent(
                receipt,
                repo_root=Path(tmp_dir),
                intent=REVIEWER_BOOTSTRAP_STARTUP_INTENT,
            )

        self.assertTrue(any("current branch" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
