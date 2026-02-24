"""Tests for devctl mutation-loop parser and command behavior."""

from __future__ import annotations

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import mutation_loop


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "repo": "owner/repo",
        "branch": "develop",
        "workflow": "Mutation Testing",
        "max_attempts": 3,
        "run_list_limit": 30,
        "poll_seconds": 20,
        "timeout_seconds": 1800,
        "mode": "report-only",
        "threshold": 0.80,
        "fix_command": None,
        "emit_bundle": False,
        "bundle_dir": ".cihub/mutation",
        "bundle_prefix": "mutation-ralph-loop",
        "notify": "summary-only",
        "comment_target": "auto",
        "comment_pr_number": None,
        "dry_run": False,
        "format": "json",
        "output": None,
        "json_output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def loop_report(*, ok: bool = True, score: float = 0.82) -> dict:
    return {
        "ok": ok,
        "repo": "owner/repo",
        "branch": "develop",
        "workflow": "Mutation Testing",
        "mode": "report-only",
        "threshold": 0.80,
        "max_attempts": 3,
        "completed_attempts": 1,
        "attempts": [
            {
                "attempt": 1,
                "run_id": 55,
                "run_sha": "a" * 40,
                "run_conclusion": "success",
                "status": "reported" if not ok else "resolved",
                "score": score,
            }
        ],
        "reason": "threshold_met" if ok else "report_only_below_threshold",
        "last_score": score,
        "fix_command_configured": False,
        "fix_block_reason": None,
    }


class MutationLoopParserTests(unittest.TestCase):
    def test_cli_accepts_mutation_loop_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "mutation-loop",
                "--repo",
                "owner/repo",
                "--branch",
                "develop",
                "--mode",
                "plan-then-fix",
                "--threshold",
                "0.85",
                "--notify",
                "summary-and-comment",
                "--comment-target",
                "pr",
                "--comment-pr-number",
                "88",
                "--format",
                "md",
            ]
        )
        self.assertEqual(args.command, "mutation-loop")
        self.assertEqual(args.repo, "owner/repo")
        self.assertEqual(args.branch, "develop")
        self.assertEqual(args.mode, "plan-then-fix")
        self.assertEqual(args.threshold, 0.85)
        self.assertEqual(args.notify, "summary-and-comment")
        self.assertEqual(args.comment_target, "pr")
        self.assertEqual(args.comment_pr_number, 88)
        self.assertEqual(args.format, "md")


class MutationLoopCommandTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.mutation_loop.write_output")
    @patch("dev.scripts.devctl.commands.mutation_loop.execute_loop")
    @patch("dev.scripts.devctl.commands.mutation_loop.load_policy", return_value={})
    @patch(
        "dev.scripts.devctl.commands.mutation_loop.shutil.which",
        return_value="/usr/bin/gh",
    )
    @patch(
        "dev.scripts.devctl.commands.mutation_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_report_only_mode_drops_fix_command(
        self,
        _resolve_repo_mock,
        _which_mock,
        _load_policy_mock,
        execute_loop_mock,
        write_output_mock,
    ) -> None:
        execute_loop_mock.return_value = loop_report(ok=False, score=0.70)
        args = make_args(mode="report-only", fix_command="echo should-not-run")
        rc = mutation_loop.run(args)
        self.assertEqual(rc, 1)
        execute_loop_mock.assert_called_once()
        self.assertIsNone(execute_loop_mock.call_args.kwargs["fix_command"])
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["fix_command_effective"])

    @patch("dev.scripts.devctl.commands.mutation_loop.write_output")
    @patch("dev.scripts.devctl.commands.mutation_loop.execute_loop")
    @patch(
        "dev.scripts.devctl.commands.mutation_loop.load_policy",
        return_value={
            "autonomy_mode_default": "read-only",
            "mutation_loop": {
                "allowed_branches": ["develop"],
                "allowed_fix_command_prefixes": [["python3", "dev/scripts/devctl.py", "check"]],
            },
        },
    )
    @patch(
        "dev.scripts.devctl.commands.mutation_loop.shutil.which",
        return_value="/usr/bin/gh",
    )
    @patch(
        "dev.scripts.devctl.commands.mutation_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_policy_denial_passes_fix_block_reason_to_loop_core(
        self,
        _resolve_repo_mock,
        _which_mock,
        _load_policy_mock,
        execute_loop_mock,
        write_output_mock,
    ) -> None:
        execute_loop_mock.return_value = loop_report(ok=False, score=0.72)
        args = make_args(
            mode="plan-then-fix",
            fix_command="python3 dev/scripts/devctl.py check --profile ci",
        )
        with patch.dict(os.environ, {"AUTONOMY_MODE": ""}, clear=False):
            rc = mutation_loop.run(args)
        self.assertEqual(rc, 1)
        fix_block_reason = execute_loop_mock.call_args.kwargs["fix_block_reason"]
        self.assertIsNotNone(fix_block_reason)
        self.assertIn("AUTONOMY_MODE", fix_block_reason or "")
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(any("AUTONOMY_MODE" in row for row in payload.get("warnings", [])))


if __name__ == "__main__":
    unittest.main()
