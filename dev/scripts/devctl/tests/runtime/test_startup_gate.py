"""Tests for scoped startup gate enforcement."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.runtime.startup_gate import (
    command_requires_startup_gate,
    enforce_startup_gate,
)
from dev.scripts.devctl.runtime.startup_receipt import StartupReceipt


def _args(command: str, *, action: str = "") -> SimpleNamespace:
    return SimpleNamespace(command=command, action=action)


class StartupGateRoutingTests(unittest.TestCase):
    def test_gate_targets_only_scoped_commands(self) -> None:
        self.assertTrue(command_requires_startup_gate(_args("push")))
        self.assertTrue(command_requires_startup_gate(_args("guard-run")))
        self.assertTrue(command_requires_startup_gate(_args("autonomy-loop")))
        self.assertTrue(command_requires_startup_gate(_args("autonomy-swarm")))
        self.assertTrue(command_requires_startup_gate(_args("mutation-loop")))
        self.assertTrue(command_requires_startup_gate(_args("swarm_run")))
        self.assertTrue(
            command_requires_startup_gate(
                _args("review-channel", action="launch")
            )
        )
        self.assertTrue(
            command_requires_startup_gate(
                _args("controller-action", action="resume-loop")
            )
        )
        self.assertFalse(command_requires_startup_gate(_args("context-graph")))
        self.assertFalse(
            command_requires_startup_gate(
                _args("review-channel", action="status")
            )
        )
        self.assertFalse(
            command_requires_startup_gate(
                _args("controller-action", action="refresh-status")
            )
        )


class StartupGateEnforcementTests(unittest.TestCase):
    @patch(
        "dev.scripts.devctl.runtime.startup_gate.build_startup_authority_report",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_gate.load_startup_receipt",
        return_value=None,
    )
    def test_gate_blocks_missing_receipt(
        self,
        _load_receipt,
        _authority_report,
    ) -> None:
        message = enforce_startup_gate(_args("push"))

        self.assertIsNotNone(message)
        self.assertIn("Startup receipt is missing", message or "")
        self.assertIn("startup-context", message or "")

    @patch(
        "dev.scripts.devctl.runtime.startup_gate.startup_receipt_problems",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_gate.build_startup_authority_report",
        return_value={"ok": False, "errors": ["over budget"]},
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_gate.load_startup_receipt",
        return_value=StartupReceipt(startup_authority_ok=True),
    )
    def test_gate_blocks_live_startup_authority_failures(
        self,
        _load_receipt,
        _authority_report,
        _receipt_problems,
    ) -> None:
        message = enforce_startup_gate(_args("review-channel", action="launch"))

        self.assertIsNotNone(message)
        self.assertIn("live startup-authority check is red", message or "")
        self.assertIn("over budget", message or "")

    @patch(
        "dev.scripts.devctl.runtime.startup_gate.startup_receipt_problems",
        return_value=["Latest startup receipt recorded startup-authority failures."],
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_gate.build_startup_authority_report",
        return_value={
            "ok": False,
            "errors": [
                "Reviewer loop blocks a new implementation slice: reviewer_mode=active_dual_agent, review_accepted=False, reason=claude_ack_stale."
            ],
            "checkpoint_required": False,
            "safe_to_continue_editing": True,
            "reviewer_loop_blocked": True,
        },
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_gate.load_startup_receipt",
        return_value=StartupReceipt(startup_authority_ok=False),
    )
    def test_gate_allows_review_channel_recovery_for_reviewer_loop_only_block(
        self,
        _load_receipt,
        _authority_report,
        _receipt_problems,
    ) -> None:
        self.assertIsNone(
            enforce_startup_gate(_args("review-channel", action="rollover"))
        )

    @patch(
        "dev.scripts.devctl.runtime.startup_gate.startup_receipt_problems",
        return_value=[
            "Latest startup receipt still requires a checkpoint before another implementation or launcher step.",
            "Latest startup receipt recorded startup-authority failures.",
        ],
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_gate.build_startup_authority_report",
        return_value={
            "ok": False,
            "errors": [
                "Reviewer loop blocks a new implementation slice: reviewer_mode=active_dual_agent, review_accepted=False, reason=claude_ack_stale."
            ],
            "checkpoint_required": True,
            "safe_to_continue_editing": False,
            "reviewer_loop_blocked": True,
        },
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_gate.load_startup_receipt",
        return_value=StartupReceipt(
            startup_authority_ok=False,
            checkpoint_required=True,
            safe_to_continue_editing=False,
        ),
    )
    def test_gate_still_blocks_recovery_when_checkpoint_is_required(
        self,
        _load_receipt,
        _authority_report,
        _receipt_problems,
    ) -> None:
        message = enforce_startup_gate(_args("review-channel", action="launch"))

        self.assertIsNotNone(message)
        self.assertIn("requires a checkpoint", message or "")

    @patch(
        "dev.scripts.devctl.runtime.startup_gate.startup_receipt_problems",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_gate.build_startup_authority_report",
        return_value={
            "ok": False,
            "errors": ["Reviewer loop blocks a new implementation slice."],
        },
    )
    @patch(
        "dev.scripts.devctl.runtime.startup_gate.load_startup_receipt",
        return_value=StartupReceipt(startup_authority_ok=True),
    )
    def test_gate_blocks_mutation_loop_when_reviewer_loop_is_stale(
        self,
        _load_receipt,
        _authority_report,
        _receipt_problems,
    ) -> None:
        message = enforce_startup_gate(_args("mutation-loop"))

        self.assertIsNotNone(message)
        self.assertIn("live startup-authority check is red", message or "")
        self.assertIn("Reviewer loop blocks", message or "")

    def test_gate_ignores_read_only_commands(self) -> None:
        self.assertIsNone(enforce_startup_gate(_args("check-router")))


if __name__ == "__main__":
    unittest.main()
