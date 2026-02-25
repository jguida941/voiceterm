"""Unit tests for mutation-loop fix-command policy gating."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from dev.scripts.devctl.mutation_loop_policy import evaluate_fix_policy


def _policy() -> dict:
    return {
        "autonomy_mode_default": "read-only",
        "mutation_loop": {
            "allowed_branches": ["develop"],
            "allowed_fix_command_prefixes": [["python3", "dev/scripts/devctl.py", "mutants"]],
        },
    }


class MutationLoopPolicyTests(unittest.TestCase):
    def test_report_only_returns_none(self) -> None:
        reason = evaluate_fix_policy(
            mode="report-only",
            branch="develop",
            fix_command="python3 dev/scripts/devctl.py mutants --module overlay",
            policy=_policy(),
        )
        self.assertIsNone(reason)

    def test_no_fix_command_returns_none(self) -> None:
        reason = evaluate_fix_policy(
            mode="plan-then-fix",
            branch="develop",
            fix_command=None,
            policy=_policy(),
        )
        self.assertIsNone(reason)

    def test_autonomy_mode_blocks(self) -> None:
        with patch.dict(os.environ, {"AUTONOMY_MODE": ""}, clear=False):
            reason = evaluate_fix_policy(
                mode="plan-then-fix",
                branch="develop",
                fix_command="python3 dev/scripts/devctl.py mutants --module overlay",
                policy=_policy(),
            )
        self.assertIsNotNone(reason)
        self.assertIn("AUTONOMY_MODE=read-only", reason or "")

    def test_branch_not_allowlisted_blocks(self) -> None:
        with patch.dict(os.environ, {"AUTONOMY_MODE": "operate"}, clear=False):
            reason = evaluate_fix_policy(
                mode="plan-then-fix",
                branch="feature/test",
                fix_command="python3 dev/scripts/devctl.py mutants --module overlay",
                policy=_policy(),
            )
        self.assertIsNotNone(reason)
        self.assertIn("branch feature/test is not allowlisted", reason or "")

    def test_allowed_prefix_matches(self) -> None:
        with patch.dict(os.environ, {"AUTONOMY_MODE": "operate"}, clear=False):
            reason = evaluate_fix_policy(
                mode="fix-only",
                branch="develop",
                fix_command="python3 dev/scripts/devctl.py mutants --module overlay --dry-run",
                policy=_policy(),
            )
        self.assertIsNone(reason)

    def test_disallowed_prefix_blocks(self) -> None:
        with patch.dict(os.environ, {"AUTONOMY_MODE": "operate"}, clear=False):
            reason = evaluate_fix_policy(
                mode="fix-only",
                branch="develop",
                fix_command="bash -lc 'echo nope'",
                policy=_policy(),
            )
        self.assertEqual(reason, "fix command blocked by allowlist policy")

    def test_env_override_prefixes(self) -> None:
        env = {
            "AUTONOMY_MODE": "operate",
            "MUTATION_LOOP_ALLOWED_PREFIXES": "bash -lc",
        }
        with patch.dict(os.environ, env, clear=False):
            reason = evaluate_fix_policy(
                mode="fix-only",
                branch="develop",
                fix_command="bash -lc 'echo allowed-by-env'",
                policy=_policy(),
            )
        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
