"""Tests for devctl sync command guardrails and workflow wiring."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import sync


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "remote": "origin",
        "branches": None,
        "no_current": False,
        "allow_dirty": False,
        "push": False,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class SyncParserTests(unittest.TestCase):
    def test_cli_accepts_sync_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "sync",
                "--remote",
                "upstream",
                "--branches",
                "develop",
                "master",
                "--no-current",
                "--allow-dirty",
                "--push",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "sync")
        self.assertEqual(args.remote, "upstream")
        self.assertEqual(args.branches, ["develop", "master"])
        self.assertTrue(args.no_current)
        self.assertTrue(args.allow_dirty)
        self.assertTrue(args.push)
        self.assertEqual(args.format, "json")


class SyncCommandTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.sync.write_output")
    @patch("dev.scripts.devctl.commands.sync.run_cmd")
    @patch("dev.scripts.devctl.commands.sync._remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.sync.collect_git_status")
    def test_sync_fails_when_tree_is_dirty(
        self,
        collect_git_status_mock,
        _remote_exists_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "branch": "develop",
            "changes": [{"status": "M", "path": "README.md"}],
        }

        rc = sync.run(make_args())

        self.assertEqual(rc, 1)
        run_cmd_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertIn("Working tree has uncommitted changes.", payload["errors"][0])

    @patch("dev.scripts.devctl.commands.sync.write_output")
    @patch("dev.scripts.devctl.commands.sync._branch_divergence")
    @patch("dev.scripts.devctl.commands.sync._remote_branch_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.sync._branch_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.sync._remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.sync.run_cmd")
    @patch("dev.scripts.devctl.commands.sync.collect_git_status")
    def test_sync_runs_fetch_pull_and_restore_starting_branch(
        self,
        collect_git_status_mock,
        run_cmd_mock,
        _remote_exists_mock,
        _branch_exists_mock,
        _remote_branch_exists_mock,
        branch_divergence_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        branch_divergence_mock.return_value = {"behind": 0, "ahead": 0, "error": None}

        def fake_run_cmd(name, cmd, cwd=None, env=None, dry_run=False):
            return {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd),
                "returncode": 0,
                "duration_s": 0.01,
                "skipped": False,
            }

        run_cmd_mock.side_effect = fake_run_cmd
        args = make_args(branches=["develop", "master"], no_current=True)

        rc = sync.run(args)

        self.assertEqual(rc, 0)
        executed_cmds = [call.args[1] for call in run_cmd_mock.call_args_list]
        self.assertEqual(executed_cmds[0], ["git", "fetch", "origin"])
        self.assertIn(["git", "pull", "--ff-only", "origin", "develop"], executed_cmds)
        self.assertIn(["git", "pull", "--ff-only", "origin", "master"], executed_cmds)
        self.assertEqual(executed_cmds[-1], ["git", "checkout", "feature/demo"])

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        statuses = {row["branch"]: row["status"] for row in payload["branches"]}
        self.assertEqual(statuses["develop"], "synced")
        self.assertEqual(statuses["master"], "synced")

    @patch("dev.scripts.devctl.commands.sync.write_output")
    @patch("dev.scripts.devctl.commands.sync._branch_divergence")
    @patch("dev.scripts.devctl.commands.sync._remote_branch_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.sync._branch_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.sync._remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.sync.run_cmd")
    @patch("dev.scripts.devctl.commands.sync.collect_git_status")
    def test_sync_with_push_clears_local_ahead_state(
        self,
        collect_git_status_mock,
        run_cmd_mock,
        _remote_exists_mock,
        _branch_exists_mock,
        _remote_branch_exists_mock,
        branch_divergence_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        branch_divergence_mock.side_effect = [
            {"behind": 0, "ahead": 2, "error": None},
            {"behind": 0, "ahead": 0, "error": None},
        ]

        def fake_run_cmd(name, cmd, cwd=None, env=None, dry_run=False):
            return {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd),
                "returncode": 0,
                "duration_s": 0.01,
                "skipped": False,
            }

        run_cmd_mock.side_effect = fake_run_cmd
        args = make_args(branches=["develop"], no_current=True, push=True)

        rc = sync.run(args)

        self.assertEqual(rc, 0)
        executed_cmds = [call.args[1] for call in run_cmd_mock.call_args_list]
        self.assertIn(["git", "push", "origin", "develop"], executed_cmds)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["branches"][0]["status"], "synced")

    @patch("dev.scripts.devctl.commands.sync.write_output")
    @patch("dev.scripts.devctl.commands.sync._branch_divergence")
    @patch("dev.scripts.devctl.commands.sync._remote_branch_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.sync._branch_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.sync._remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.sync.run_cmd")
    @patch("dev.scripts.devctl.commands.sync.collect_git_status")
    def test_sync_without_push_fails_when_branch_is_ahead(
        self,
        collect_git_status_mock,
        run_cmd_mock,
        _remote_exists_mock,
        _branch_exists_mock,
        _remote_branch_exists_mock,
        branch_divergence_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        branch_divergence_mock.return_value = {"behind": 0, "ahead": 1, "error": None}

        def fake_run_cmd(name, cmd, cwd=None, env=None, dry_run=False):
            return {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd),
                "returncode": 0,
                "duration_s": 0.01,
                "skipped": False,
            }

        run_cmd_mock.side_effect = fake_run_cmd
        args = make_args(branches=["develop"], no_current=True, push=False)

        rc = sync.run(args)

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["branches"][0]["status"], "ahead")


if __name__ == "__main__":
    unittest.main()
