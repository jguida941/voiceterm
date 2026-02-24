"""Tests for `devctl failure-cleanup` command behavior."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import failure_cleanup


class FailureCleanupParserTests(TestCase):
    def test_cli_accepts_failure_cleanup_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "failure-cleanup",
                "--dry-run",
                "--require-green-ci",
                "--ci-branch",
                "develop",
                "--ci-workflow",
                "Rust TUI CI",
                "--ci-event",
                "push",
                "--ci-sha",
                "abc123",
            ]
        )
        self.assertEqual(args.command, "failure-cleanup")
        self.assertTrue(args.dry_run)
        self.assertTrue(args.require_green_ci)
        self.assertEqual(args.ci_branch, "develop")
        self.assertEqual(args.ci_workflow, "Rust TUI CI")
        self.assertEqual(args.ci_event, "push")
        self.assertEqual(args.ci_sha, "abc123")


class FailureCleanupCommandTests(TestCase):
    @patch("dev.scripts.devctl.commands.failure_cleanup.write_output")
    @patch("dev.scripts.devctl.commands.failure_cleanup.collect_ci_runs")
    def test_failure_cleanup_dry_run_keeps_directory(
        self,
        collect_ci_runs_mock,
        write_output_mock,
    ) -> None:
        collect_ci_runs_mock.return_value = {"runs": []}
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            target = repo_root / "dev/reports/failures/workflow/run-1"
            target.mkdir(parents=True)
            (target / "triage.md").write_text("# triage\n", encoding="utf-8")

            args = SimpleNamespace(
                directory="dev/reports/failures",
                allow_outside_failure_root=False,
                require_green_ci=False,
                ci_limit=5,
                ci_branch=None,
                ci_workflow=None,
                ci_event=None,
                ci_sha=None,
                yes=True,
                dry_run=True,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
            )
            with patch("dev.scripts.devctl.commands.failure_cleanup.REPO_ROOT", repo_root):
                code = failure_cleanup.run(args)

        self.assertEqual(code, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["files_found"], 1)
        self.assertFalse(payload["deleted"])

    @patch("dev.scripts.devctl.commands.failure_cleanup.write_output")
    @patch("dev.scripts.devctl.commands.failure_cleanup.collect_ci_runs")
    def test_failure_cleanup_blocks_when_recent_ci_has_failures(
        self,
        collect_ci_runs_mock,
        write_output_mock,
    ) -> None:
        collect_ci_runs_mock.return_value = {
            "runs": [
                {
                    "displayTitle": "Rust TUI CI",
                    "status": "completed",
                    "conclusion": "failure",
                    "updatedAt": "2026-02-23T10:00:00Z",
                    "headSha": "abc123",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            target = repo_root / "dev/reports/failures"
            target.mkdir(parents=True)

            args = SimpleNamespace(
                directory="dev/reports/failures",
                allow_outside_failure_root=False,
                require_green_ci=True,
                ci_limit=5,
                ci_branch=None,
                ci_workflow=None,
                ci_event=None,
                ci_sha=None,
                yes=True,
                dry_run=True,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
            )
            with patch("dev.scripts.devctl.commands.failure_cleanup.REPO_ROOT", repo_root):
                code = failure_cleanup.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ci_gate_ok"])
        self.assertEqual(len(payload["blocking_ci_runs"]), 1)

    @patch("dev.scripts.devctl.commands.failure_cleanup.write_output")
    @patch("dev.scripts.devctl.commands.failure_cleanup.collect_ci_runs")
    def test_failure_cleanup_deletes_directory_when_green_and_confirmed(
        self,
        collect_ci_runs_mock,
        write_output_mock,
    ) -> None:
        collect_ci_runs_mock.return_value = {
            "runs": [
                {
                    "displayTitle": "Rust TUI CI",
                    "status": "completed",
                    "conclusion": "success",
                    "updatedAt": "2026-02-23T10:00:00Z",
                    "headSha": "abc123",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            target = repo_root / "dev/reports/failures/workflow/run-1"
            target.mkdir(parents=True)
            (target / "triage.md").write_text("# triage\n", encoding="utf-8")

            args = SimpleNamespace(
                directory="dev/reports/failures",
                allow_outside_failure_root=False,
                require_green_ci=True,
                ci_limit=5,
                ci_branch=None,
                ci_workflow=None,
                ci_event=None,
                ci_sha=None,
                yes=True,
                dry_run=False,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
            )
            with patch("dev.scripts.devctl.commands.failure_cleanup.REPO_ROOT", repo_root):
                code = failure_cleanup.run(args)
                self.assertFalse((repo_root / "dev/reports/failures").exists())

        self.assertEqual(code, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["deleted"])
        self.assertTrue(payload["ok"])

    @patch("dev.scripts.devctl.commands.failure_cleanup.write_output")
    def test_failure_cleanup_rejects_directory_outside_failure_root_by_default(
        self,
        write_output_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            outside_dir = repo_root / "tmp/failure-audit"
            outside_dir.mkdir(parents=True)

            args = SimpleNamespace(
                directory="tmp/failure-audit",
                allow_outside_failure_root=False,
                require_green_ci=False,
                ci_limit=5,
                ci_branch=None,
                ci_workflow=None,
                ci_event=None,
                ci_sha=None,
                yes=True,
                dry_run=True,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
            )
            with patch("dev.scripts.devctl.commands.failure_cleanup.REPO_ROOT", repo_root):
                code = failure_cleanup.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertTrue(any("outside default failure root" in msg for msg in payload["errors"]))

    @patch("dev.scripts.devctl.commands.failure_cleanup.write_output")
    def test_failure_cleanup_allows_outside_failure_root_with_override(
        self,
        write_output_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            outside_dir = repo_root / "dev/reports/archive-failures"
            outside_dir.mkdir(parents=True)
            (outside_dir / "artifact.md").write_text("x", encoding="utf-8")

            args = SimpleNamespace(
                directory="dev/reports/archive-failures",
                allow_outside_failure_root=True,
                require_green_ci=False,
                ci_limit=5,
                ci_branch=None,
                ci_workflow=None,
                ci_event=None,
                ci_sha=None,
                yes=True,
                dry_run=True,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
            )
            with patch("dev.scripts.devctl.commands.failure_cleanup.REPO_ROOT", repo_root):
                code = failure_cleanup.run(args)

        self.assertEqual(code, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["allow_outside_failure_root"])

    @patch("dev.scripts.devctl.commands.failure_cleanup.write_output")
    def test_failure_cleanup_override_rejects_non_reports_directory(
        self,
        write_output_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            outside_dir = repo_root / "tmp/failure-audit"
            outside_dir.mkdir(parents=True)

            args = SimpleNamespace(
                directory="tmp/failure-audit",
                allow_outside_failure_root=True,
                require_green_ci=False,
                ci_limit=5,
                ci_branch=None,
                ci_workflow=None,
                ci_event=None,
                ci_sha=None,
                yes=True,
                dry_run=True,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
            )
            with patch("dev.scripts.devctl.commands.failure_cleanup.REPO_ROOT", repo_root):
                code = failure_cleanup.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertTrue(any("outside allowed override root" in msg for msg in payload["errors"]))

    @patch("dev.scripts.devctl.commands.failure_cleanup.write_output")
    def test_failure_cleanup_override_rejects_git_directory(
        self,
        write_output_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            git_dir = repo_root / ".git"
            git_dir.mkdir(parents=True)

            args = SimpleNamespace(
                directory=".git",
                allow_outside_failure_root=True,
                require_green_ci=False,
                ci_limit=5,
                ci_branch=None,
                ci_workflow=None,
                ci_event=None,
                ci_sha=None,
                yes=True,
                dry_run=True,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
            )
            with patch("dev.scripts.devctl.commands.failure_cleanup.REPO_ROOT", repo_root):
                code = failure_cleanup.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertTrue(any("refusing to delete .git" in msg for msg in payload["errors"]))

    @patch("dev.scripts.devctl.commands.failure_cleanup.write_output")
    @patch("dev.scripts.devctl.commands.failure_cleanup.collect_ci_runs")
    def test_failure_cleanup_ci_filters_fail_safe_when_no_runs_match(
        self,
        collect_ci_runs_mock,
        write_output_mock,
    ) -> None:
        collect_ci_runs_mock.return_value = {
            "runs": [
                {
                    "displayTitle": "Rust TUI CI",
                    "name": "rust_ci.yml",
                    "event": "push",
                    "headBranch": "develop",
                    "headSha": "abc123",
                    "status": "completed",
                    "conclusion": "success",
                    "updatedAt": "2026-02-23T10:00:00Z",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            target = repo_root / "dev/reports/failures"
            target.mkdir(parents=True)

            args = SimpleNamespace(
                directory="dev/reports/failures",
                allow_outside_failure_root=False,
                require_green_ci=True,
                ci_limit=5,
                ci_branch="master",
                ci_workflow=None,
                ci_event=None,
                ci_sha=None,
                yes=True,
                dry_run=True,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
            )
            with patch("dev.scripts.devctl.commands.failure_cleanup.REPO_ROOT", repo_root):
                code = failure_cleanup.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["ci_matched_runs"], 0)
        self.assertFalse(payload["ci_gate_ok"])
        self.assertIn("No CI runs matched", payload["ci_error"])
