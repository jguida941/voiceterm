"""Tests for `devctl guard-run` command behavior."""

from __future__ import annotations

import json
from unittest import TestCase, mock

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import guard_run
from dev.scripts.devctl.config import REPO_ROOT


class GuardRunParserTests(TestCase):
    def test_cli_accepts_guard_run_flags_and_command(self) -> None:
        args = build_parser().parse_args(
            [
                "guard-run",
                "--cwd",
                "rust",
                "--post-action",
                "quick",
                "--format",
                "json",
                "--",
                "cargo",
                "test",
                "--bin",
                "voiceterm",
            ]
        )

        self.assertEqual(args.command, "guard-run")
        self.assertEqual(args.cwd, "rust")
        self.assertEqual(args.post_action, "quick")
        self.assertEqual(args.guarded_command, ["--", "cargo", "test", "--bin", "voiceterm"])


class GuardRunCommandTests(TestCase):
    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_auto_runtime_command_runs_quick_followup(
        self,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        run_cmd_mock.side_effect = [
            {"returncode": 0},
            {"returncode": 0},
        ]
        args = build_parser().parse_args(
            [
                "guard-run",
                "--cwd",
                "rust",
                "--format",
                "json",
                "--",
                "cargo",
                "test",
                "--bin",
                "voiceterm",
                "banner::tests",
                "--",
                "--nocapture",
            ]
        )

        rc = guard_run.run(args)

        self.assertEqual(rc, 0)
        first_call = run_cmd_mock.call_args_list[0]
        self.assertEqual(first_call.args[0], "guarded-command")
        self.assertEqual(
            first_call.args[1],
            ["cargo", "test", "--bin", "voiceterm", "banner::tests", "--", "--nocapture"],
        )
        self.assertEqual(first_call.kwargs["cwd"], REPO_ROOT / "rust")
        second_call = run_cmd_mock.call_args_list[1]
        self.assertEqual(second_call.args[1], guard_run.QUICK_FOLLOWUP_CMD)
        self.assertEqual(second_call.kwargs["cwd"], REPO_ROOT)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["resolved_post_action"], "quick")
        self.assertTrue(payload["ok"])

    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_auto_tooling_command_runs_cleanup_followup(
        self,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        run_cmd_mock.side_effect = [
            {"returncode": 0},
            {"returncode": 0},
        ]
        args = build_parser().parse_args(
            [
                "guard-run",
                "--format",
                "json",
                "--",
                "python3",
                "dev/scripts/devctl.py",
                "docs-check",
                "--strict-tooling",
            ]
        )

        rc = guard_run.run(args)

        self.assertEqual(rc, 0)
        second_call = run_cmd_mock.call_args_list[1]
        self.assertEqual(second_call.args[1], guard_run.CLEANUP_FOLLOWUP_CMD)
        self.assertEqual(second_call.kwargs["cwd"], REPO_ROOT)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["resolved_post_action"], "cleanup")

    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_shell_c_wrapper_is_rejected(
        self,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        args = build_parser().parse_args(
            [
                "guard-run",
                "--format",
                "json",
                "--",
                "zsh",
                "-c",
                "cargo test --bin voiceterm",
            ]
        )

        rc = guard_run.run(args)

        self.assertEqual(rc, 1)
        run_cmd_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertIn("Shell `-c` wrappers are not allowed", payload["errors"][0])

    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_out_of_repo_cwd_is_rejected(
        self,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        args = build_parser().parse_args(
            [
                "guard-run",
                "--cwd",
                "/tmp/other-checkout",
                "--format",
                "json",
                "--",
                "python3",
                "dev/scripts/devctl.py",
                "docs-check",
                "--strict-tooling",
            ]
        )

        rc = guard_run.run(args)

        self.assertEqual(rc, 1)
        run_cmd_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertIn("outside this checkout", payload["errors"][0])

    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    @mock.patch("dev.scripts.devctl.commands.guard_run.path_is_under_repo")
    def test_repo_containment_uses_process_sweep_helper(
        self,
        path_is_under_repo_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        path_is_under_repo_mock.return_value = False
        args = build_parser().parse_args(
            [
                "guard-run",
                "--cwd",
                "rust",
                "--format",
                "json",
                "--",
                "cargo",
                "test",
                "--bin",
                "voiceterm",
            ]
        )

        rc = guard_run.run(args)

        self.assertEqual(rc, 1)
        path_is_under_repo_mock.assert_called_once_with(str(REPO_ROOT / "rust"))
        run_cmd_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertIn("outside this checkout", payload["errors"][0])

    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_command_failure_still_runs_followup(
        self,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        run_cmd_mock.side_effect = [
            {"returncode": 101},
            {"returncode": 0},
        ]
        args = build_parser().parse_args(
            [
                "guard-run",
                "--format",
                "json",
                "--",
                "cargo",
                "test",
                "--manifest-path",
                "rust/Cargo.toml",
                "--bin",
                "voiceterm",
                "banner::tests",
            ]
        )

        rc = guard_run.run(args)

        self.assertEqual(rc, 1)
        self.assertEqual(run_cmd_mock.call_count, 2)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["resolved_post_action"], "quick")
        self.assertIn("Guarded command failed", payload["errors"][0])
