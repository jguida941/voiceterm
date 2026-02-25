"""Tests for devctl triage-loop parser and command behavior."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import triage_loop


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "repo": "owner/repo",
        "branch": "develop",
        "workflow": "CodeRabbit Triage Bridge",
        "max_attempts": 3,
        "run_list_limit": 30,
        "poll_seconds": 20,
        "timeout_seconds": 1800,
        "mode": "plan-then-fix",
        "fix_command": "python3 dev/scripts/devctl.py check --profile ci",
        "emit_bundle": False,
        "bundle_dir": ".cihub/coderabbit",
        "bundle_prefix": "coderabbit-ralph-loop",
        "mp_proposal": False,
        "mp_proposal_path": None,
        "notify": "summary-only",
        "comment_target": "auto",
        "comment_pr_number": None,
        "source_run_id": None,
        "source_run_sha": None,
        "source_event": "workflow_dispatch",
        "dry_run": False,
        "format": "json",
        "output": None,
        "json_output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def loop_report(*, ok: bool = True, unresolved: int = 0) -> dict:
    return {
        "ok": ok,
        "repo": "owner/repo",
        "branch": "develop",
        "workflow": "CodeRabbit Triage Bridge",
        "max_attempts": 3,
        "completed_attempts": 1,
        "attempts": [
            {
                "attempt": 1,
                "run_id": 123,
                "run_sha": "a" * 40,
                "run_url": "https://example.invalid/run/123",
                "run_conclusion": "success" if ok else "failure",
                "backlog_count": unresolved,
                "status": "resolved" if unresolved == 0 else "blocked",
            }
        ],
        "unresolved_count": unresolved,
        "reason": "resolved" if unresolved == 0 else "no fix command configured",
        "fix_command_configured": True,
        "fix_block_reason": None,
        "escalation_needed": False,
    }


class TriageLoopParserTests(unittest.TestCase):
    def test_cli_accepts_triage_loop_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "triage-loop",
                "--repo",
                "owner/repo",
                "--branch",
                "develop",
                "--mode",
                "report-only",
                "--emit-bundle",
                "--mp-proposal",
                "--notify",
                "summary-and-comment",
                "--comment-target",
                "pr",
                "--comment-pr-number",
                "123",
                "--source-event",
                "workflow_run",
                "--source-run-id",
                "456",
                "--source-run-sha",
                "abcdef1234",
                "--format",
                "md",
            ]
        )
        self.assertEqual(args.command, "triage-loop")
        self.assertEqual(args.repo, "owner/repo")
        self.assertEqual(args.branch, "develop")
        self.assertEqual(args.mode, "report-only")
        self.assertTrue(args.emit_bundle)
        self.assertTrue(args.mp_proposal)
        self.assertEqual(args.notify, "summary-and-comment")
        self.assertEqual(args.comment_target, "pr")
        self.assertEqual(args.comment_pr_number, 123)
        self.assertEqual(args.source_event, "workflow_run")
        self.assertEqual(args.source_run_id, 456)
        self.assertEqual(args.source_run_sha, "abcdef1234")
        self.assertEqual(args.format, "md")


class TriageLoopCommandTests(unittest.TestCase):
    @patch(
        "dev.scripts.devctl.commands.triage_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_workflow_run_requires_source_run_id(self, _resolve_repo_mock) -> None:
        args = make_args(source_event="workflow_run", source_run_id=None)
        rc = triage_loop.run(args)
        self.assertEqual(rc, 2)

    @patch("dev.scripts.devctl.commands.triage_loop.write_output")
    @patch("dev.scripts.devctl.commands.triage_loop.execute_loop")
    @patch(
        "dev.scripts.devctl.commands.triage_loop.run_capture",
        return_value=(0, "1000", ""),
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.shutil.which",
        return_value="/usr/bin/gh",
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_report_only_mode_drops_fix_command(
        self,
        _resolve_repo_mock,
        _which_mock,
        _run_capture_mock,
        execute_loop_mock,
        write_output_mock,
    ) -> None:
        execute_loop_mock.return_value = loop_report(ok=False, unresolved=2)
        args = make_args(mode="report-only", fix_command="echo should-not-run")
        rc = triage_loop.run(args)
        self.assertEqual(rc, 1)
        execute_loop_mock.assert_called_once()
        self.assertIsNone(execute_loop_mock.call_args.kwargs["fix_command"])
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["fix_command_effective"])

    @patch("dev.scripts.devctl.commands.triage_loop.write_output")
    @patch("dev.scripts.devctl.commands.triage_loop.execute_loop")
    @patch(
        "dev.scripts.devctl.commands.triage_loop.load_policy",
        return_value={
            "autonomy_mode_default": "read-only",
            "triage_loop": {
                "allowed_branches": ["develop"],
                "allowed_fix_command_prefixes": [
                    ["python3", "dev/scripts/devctl.py", "check", "--profile", "ci"]
                ],
            },
        },
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.run_capture",
        return_value=(0, "1000", ""),
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.shutil.which",
        return_value="/usr/bin/gh",
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_policy_denial_passes_fix_block_reason_to_loop_core(
        self,
        _resolve_repo_mock,
        _which_mock,
        _run_capture_mock,
        _load_policy_mock,
        execute_loop_mock,
        write_output_mock,
    ) -> None:
        execute_loop_mock.return_value = loop_report(ok=False, unresolved=2)
        args = make_args(
            mode="plan-then-fix",
            fix_command="python3 dev/scripts/devctl.py check --profile ci",
        )
        with patch.dict(os.environ, {"AUTONOMY_MODE": ""}, clear=False):
            rc = triage_loop.run(args)
        self.assertEqual(rc, 1)
        fix_block_reason = execute_loop_mock.call_args.kwargs["fix_block_reason"]
        self.assertIsNotNone(fix_block_reason)
        self.assertIn("AUTONOMY_MODE", fix_block_reason or "")
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(any("AUTONOMY_MODE" in row for row in payload.get("warnings", [])))

    @patch("dev.scripts.devctl.commands.triage_loop.write_output")
    @patch("dev.scripts.devctl.commands.triage_loop.execute_loop")
    @patch(
        "dev.scripts.devctl.commands.triage_loop.run_capture",
        return_value=(1, "", "error connecting to api.github.com"),
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop._is_ci_environment",
        return_value=False,
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.shutil.which",
        return_value="/usr/bin/gh",
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_preflight_connectivity_is_non_blocking_locally(
        self,
        _resolve_repo_mock,
        _which_mock,
        _is_ci_mock,
        _run_capture_mock,
        execute_loop_mock,
        write_output_mock,
    ) -> None:
        args = make_args(mode="report-only")
        rc = triage_loop.run(args)
        self.assertEqual(rc, 0)
        execute_loop_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["reason"], "gh_unreachable_local_non_blocking")

    @patch("dev.scripts.devctl.commands.triage_loop.write_output")
    @patch("dev.scripts.devctl.commands.triage_loop.execute_loop")
    @patch(
        "dev.scripts.devctl.commands.triage_loop.run_capture",
        return_value=(0, "1000", ""),
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop._is_ci_environment",
        return_value=False,
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.shutil.which",
        return_value="/usr/bin/gh",
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_connectivity_reason_is_normalized_to_non_blocking_locally(
        self,
        _resolve_repo_mock,
        _which_mock,
        _is_ci_mock,
        _run_capture_mock,
        execute_loop_mock,
        write_output_mock,
    ) -> None:
        execute_loop_mock.return_value = {
            **loop_report(ok=False, unresolved=0),
            "reason": "timeout waiting for completed run (error connecting to api.github.com)",
        }
        args = make_args(mode="report-only")
        rc = triage_loop.run(args)
        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["reason"], "gh_unreachable_local_non_blocking")

    @patch("dev.scripts.devctl.commands.triage_loop.write_output")
    @patch("dev.scripts.devctl.commands.triage_loop.execute_loop")
    @patch(
        "dev.scripts.devctl.commands.triage_loop.run_capture",
        return_value=(0, "1000", ""),
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.shutil.which",
        return_value="/usr/bin/gh",
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_emit_bundle_writes_report_and_mp_proposal(
        self,
        _resolve_repo_mock,
        _which_mock,
        _run_capture_mock,
        execute_loop_mock,
        write_output_mock,
    ) -> None:
        execute_loop_mock.return_value = loop_report(ok=True, unresolved=0)
        with tempfile.TemporaryDirectory() as tmp_dir:
            args = make_args(
                emit_bundle=True,
                bundle_dir=tmp_dir,
                bundle_prefix="loop-pack",
                mp_proposal=True,
                mode="plan-then-fix",
                output=None,
            )
            rc = triage_loop.run(args)
            self.assertEqual(rc, 0)
            write_output_mock.assert_called_once()

            md_path = Path(tmp_dir) / "loop-pack.md"
            json_path = Path(tmp_dir) / "loop-pack.json"
            mp_path = Path(tmp_dir) / "loop-pack-master-plan-proposal.md"
            self.assertTrue(md_path.exists())
            self.assertTrue(json_path.exists())
            self.assertTrue(mp_path.exists())

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["command"], "triage-loop")
            self.assertEqual(payload["mode"], "plan-then-fix")
            self.assertTrue(payload["bundle"]["written"])

    @patch("dev.scripts.devctl.commands.triage_loop.write_output")
    @patch(
        "dev.scripts.devctl.commands.triage_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_dry_run_skips_execute_loop_and_writes_report(
        self,
        _resolve_repo_mock,
        write_output_mock,
    ) -> None:
        args = make_args(dry_run=True, mode="fix-only", fix_command=None)
        rc = triage_loop.run(args)
        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["reason"], "dry-run")

    @patch("dev.scripts.devctl.commands.triage_loop.write_output")
    @patch("dev.scripts.devctl.commands.triage_loop._publish_notification_comment")
    @patch("dev.scripts.devctl.commands.triage_loop.execute_loop")
    @patch(
        "dev.scripts.devctl.commands.triage_loop.run_capture",
        return_value=(0, "1000", ""),
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.shutil.which",
        return_value="/usr/bin/gh",
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_summary_and_comment_failure_marks_report_failed(
        self,
        _resolve_repo_mock,
        _which_mock,
        _run_capture_mock,
        execute_loop_mock,
        publish_mock,
        write_output_mock,
    ) -> None:
        execute_loop_mock.return_value = loop_report(ok=True, unresolved=0)
        publish_mock.return_value = {"ok": False, "error": "comment denied"}
        args = make_args(notify="summary-and-comment")
        rc = triage_loop.run(args)
        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["reason"], "notification_comment_failed")
        self.assertIn("comment denied", " ".join(payload.get("warnings", [])))

    @patch("dev.scripts.devctl.commands.triage_loop.write_output")
    @patch("dev.scripts.devctl.commands.triage_loop._publish_review_escalation")
    @patch("dev.scripts.devctl.commands.triage_loop._publish_notification_comment")
    @patch("dev.scripts.devctl.commands.triage_loop.execute_loop")
    @patch(
        "dev.scripts.devctl.commands.triage_loop.run_capture",
        return_value=(0, "1000", ""),
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.shutil.which",
        return_value="/usr/bin/gh",
    )
    @patch(
        "dev.scripts.devctl.commands.triage_loop.resolve_repo",
        return_value="owner/repo",
    )
    def test_escalation_comment_published_when_attempts_exhausted(
        self,
        _resolve_repo_mock,
        _which_mock,
        _run_capture_mock,
        execute_loop_mock,
        publish_notification_mock,
        publish_escalation_mock,
        write_output_mock,
    ) -> None:
        execute_loop_mock.return_value = {
            **loop_report(ok=False, unresolved=3),
            "reason": "max attempts reached with unresolved medium+ backlog",
            "escalation_needed": True,
        }
        publish_notification_mock.return_value = {"ok": True, "mode": "summary-and-comment"}
        publish_escalation_mock.return_value = {"ok": True, "mode": "summary-and-comment"}
        args = make_args(notify="summary-and-comment")
        rc = triage_loop.run(args)
        self.assertEqual(rc, 1)
        publish_escalation_mock.assert_called_once()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertIn("escalation_result", payload)


if __name__ == "__main__":
    unittest.main()
