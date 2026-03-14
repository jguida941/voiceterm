"""Tests for `devctl guard-run` command behavior."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase, mock

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import guard_run
from dev.scripts.devctl.config import REPO_ROOT
from dev.scripts.devctl.watchdog.episode import build_guarded_coding_episode


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
        self.assertIsNone(args.provider)
        self.assertEqual(args.retry_count, 0)


class GuardRunCommandTests(TestCase):
    @mock.patch("dev.scripts.devctl.commands.guard_run.emit_guarded_coding_episode")
    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_auto_runtime_command_runs_quick_followup(
        self,
        run_cmd_mock,
        write_output_mock,
        emit_episode_mock,
    ) -> None:
        run_cmd_mock.side_effect = [
            {"returncode": 0},
            {"returncode": 0},
        ]
        emit_episode_mock.return_value = str(
            REPO_ROOT / "dev/reports/autonomy/watchdog/episodes/episode-123/summary.json"
        )
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
        self.assertIn("watchdog_summary_path", payload)

    @mock.patch("dev.scripts.devctl.commands.guard_run.emit_guarded_coding_episode")
    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_auto_tooling_command_runs_cleanup_followup(
        self,
        run_cmd_mock,
        write_output_mock,
        emit_episode_mock,
    ) -> None:
        run_cmd_mock.side_effect = [
            {"returncode": 0},
            {"returncode": 0},
        ]
        emit_episode_mock.return_value = None
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

    @mock.patch("dev.scripts.devctl.commands.guard_run.emit_guarded_coding_episode")
    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_shell_c_wrapper_is_rejected(
        self,
        run_cmd_mock,
        write_output_mock,
        emit_episode_mock,
    ) -> None:
        emit_episode_mock.return_value = None
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
        emit_episode_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertIn("Shell `-c` wrappers are not allowed", payload["errors"][0])

    @mock.patch("dev.scripts.devctl.commands.guard_run.emit_guarded_coding_episode")
    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_out_of_repo_cwd_is_rejected(
        self,
        run_cmd_mock,
        write_output_mock,
        emit_episode_mock,
    ) -> None:
        emit_episode_mock.return_value = None
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

    @mock.patch("dev.scripts.devctl.commands.guard_run.emit_guarded_coding_episode")
    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    @mock.patch("dev.scripts.devctl.commands.guard_run.path_is_under_repo")
    def test_repo_containment_uses_process_sweep_helper(
        self,
        path_is_under_repo_mock,
        run_cmd_mock,
        write_output_mock,
        emit_episode_mock,
    ) -> None:
        path_is_under_repo_mock.return_value = False
        emit_episode_mock.return_value = None
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

    @mock.patch("dev.scripts.devctl.commands.guard_run.emit_guarded_coding_episode")
    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_command_failure_still_runs_followup(
        self,
        run_cmd_mock,
        write_output_mock,
        emit_episode_mock,
    ) -> None:
        run_cmd_mock.side_effect = [
            {"returncode": 101},
            {"returncode": 0},
        ]
        emit_episode_mock.return_value = None
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

    @mock.patch("dev.scripts.devctl.commands.guard_run.emit_guarded_coding_episode")
    @mock.patch("dev.scripts.devctl.commands.guard_run.write_output")
    @mock.patch("dev.scripts.devctl.commands.guard_run.run_cmd")
    def test_watchdog_emit_failure_only_adds_warning(
        self,
        run_cmd_mock,
        write_output_mock,
        emit_episode_mock,
    ) -> None:
        run_cmd_mock.side_effect = [{"returncode": 0}, {"returncode": 0}]
        emit_episode_mock.side_effect = OSError("disk full")
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
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertIn("Watchdog episode emit skipped", payload["warnings"][0])


class WatchdogEpisodeTests(TestCase):
    def test_build_guarded_coding_episode_maps_guard_run_report(self) -> None:
        episode = build_guarded_coding_episode(
            {
                "label": "guarded-command",
                "cwd": str(REPO_ROOT / "rust"),
                "ok": True,
                "command_args": ["cargo", "test", "--bin", "voiceterm"],
                "command_display": "cargo test --bin voiceterm",
                "guard_started_at_utc": "2026-03-10T01:00:00Z",
                "guard_finished_at_utc": "2026-03-10T01:00:05Z",
                "guard_runtime_seconds": 5.0,
                "resolved_post_action": "quick",
                "watchdog_context": {
                    "provider": "claude",
                    "session_id": "session-a",
                    "peer_session_id": "session-b",
                    "trigger_reason": "pre_handoff_validation",
                    "retry_count": 2,
                    "escaped_findings_count": 1,
                    "guard_result": "noisy",
                    "reviewer_verdict": "accepted_with_followups",
                },
                "diff_snapshot_before": {
                    "reviewed_worktree_hash": "abc123",
                    "files_changed": ["rust/src/main.rs"],
                    "file_count": 1,
                    "lines_added": 7,
                    "lines_removed": 2,
                    "diff_churn": 9,
                },
                "diff_snapshot_after": {
                    "reviewed_worktree_hash": "abc123",
                    "files_changed": ["rust/src/main.rs"],
                    "file_count": 1,
                    "lines_added": 4,
                    "lines_removed": 1,
                    "diff_churn": 5,
                },
            }
        )

        self.assertEqual(episode.guard_family, "rust")
        self.assertEqual(episode.guard_result, "noisy")
        self.assertEqual(episode.reviewer_verdict, "accepted_with_followups")
        self.assertEqual(episode.time_to_green_seconds, 5.0)
        self.assertEqual(episode.file_count, 1)
        self.assertEqual(episode.lines_added_before_guard, 7)
        self.assertEqual(episode.diff_churn_after_guard, 5)
        self.assertEqual(episode.reviewed_worktree_hash_before, "abc123")
        self.assertEqual(episode.test_runtime_seconds, 5.0)
        self.assertEqual(episode.provider, "claude")
        self.assertEqual(episode.session_id, "session-a")
        self.assertEqual(episode.peer_session_id, "session-b")
        self.assertEqual(episode.trigger_reason, "pre_handoff_validation")
        self.assertEqual(episode.retry_count, 2)
        self.assertEqual(episode.escaped_findings_count, 1)

    def test_guard_run_emits_watchdog_artifact_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            args = build_parser().parse_args(
                [
                    "guard-run",
                    "--provider",
                    "codex",
                    "--session-id",
                    "session-1",
                    "--peer-session-id",
                    "session-2",
                    "--trigger-reason",
                    "pre_handoff_validation",
                    "--retry-count",
                    "3",
                    "--escaped-findings-count",
                    "1",
                    "--guard-result",
                    "noisy",
                    "--reviewer-verdict",
                    "accepted_with_followups",
                    "--format",
                    "json",
                    "--",
                    "python3",
                    "dev/scripts/devctl.py",
                    "docs-check",
                    "--strict-tooling",
                ]
            )
            with (
                mock.patch.dict(
                    "os.environ",
                    {"DEVCTL_WATCHDOG_EPISODE_ROOT": str(root)},
                    clear=False,
                ),
                mock.patch(
                    "dev.scripts.devctl.commands.guard_run.run_cmd",
                    side_effect=[{"returncode": 0}, {"returncode": 0}],
                ),
                mock.patch("dev.scripts.devctl.commands.guard_run.write_output") as write_output_mock,
            ):
                rc = guard_run.run(args)

            self.assertEqual(rc, 0)
            jsonl_path = root / "guarded_coding_episode.jsonl"
            self.assertTrue(jsonl_path.exists())
            rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["guard_family"], "docs")
            self.assertEqual(rows[0]["provider"], "codex")
            self.assertEqual(rows[0]["session_id"], "session-1")
            self.assertEqual(rows[0]["peer_session_id"], "session-2")
            self.assertEqual(rows[0]["trigger_reason"], "pre_handoff_validation")
            self.assertEqual(rows[0]["retry_count"], 3)
            self.assertEqual(rows[0]["escaped_findings_count"], 1)
            self.assertEqual(rows[0]["guard_result"], "noisy")
            self.assertEqual(rows[0]["reviewer_verdict"], "accepted_with_followups")
            payload = json.loads(write_output_mock.call_args.args[0])
            summary_path = Path(payload["watchdog_summary_path"])
            self.assertTrue(summary_path.exists())
