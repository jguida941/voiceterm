"""Tests for `devctl process-audit` command behavior."""

from __future__ import annotations

import json
from unittest import TestCase, mock

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import process_audit


class ProcessAuditParserTests(TestCase):
    def test_cli_accepts_process_audit_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["process-audit", "--strict", "--format", "json"])

        self.assertEqual(args.command, "process-audit")
        self.assertTrue(args.strict)
        self.assertEqual(args.format, "json")


class ProcessAuditCommandTests(TestCase):
    @mock.patch("dev.scripts.devctl.commands.process_audit.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_audit.scan_repo_hygiene_process_tree"
    )
    def test_run_returns_zero_when_no_processes_are_detected(
        self,
        scan_mock,
        write_output_mock,
    ) -> None:
        scan_mock.return_value = ([], [])
        args = build_parser().parse_args(["process-audit", "--format", "json"])

        rc = process_audit.run(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["total_detected"], 0)

    @mock.patch("dev.scripts.devctl.commands.process_audit.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_audit.scan_repo_hygiene_process_tree"
    )
    def test_run_strict_fails_when_active_recent_processes_exist(
        self,
        scan_mock,
        write_output_mock,
    ) -> None:
        scan_mock.return_value = (
            [
                {
                    "pid": 100,
                    "ppid": 50,
                    "etime": "05:00",
                    "elapsed_seconds": 300,
                    "command": "cargo test --bin voiceterm",
                    "match_source": "direct",
                    "match_scope": "voiceterm",
                },
                {
                    "pid": 101,
                    "ppid": 100,
                    "etime": "04:59",
                    "elapsed_seconds": 299,
                    "command": "cat",
                    "match_source": "descendant",
                    "match_scope": "voiceterm",
                },
            ],
            [],
        )
        args = build_parser().parse_args(["process-audit", "--strict", "--format", "json"])

        rc = process_audit.run(args)

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["active_recent_count"], 2)
        self.assertIn(
            "Active runtime/test repo-related host processes",
            payload["errors"][0],
        )

    @mock.patch("dev.scripts.devctl.commands.process_audit.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_audit.scan_repo_hygiene_process_tree"
    )
    def test_run_fails_when_host_scan_is_unavailable(
        self,
        scan_mock,
        write_output_mock,
    ) -> None:
        scan_mock.return_value = ([], ["Process sweep skipped: ps returned 1 (denied)"])
        args = build_parser().parse_args(["process-audit", "--format", "json"])

        rc = process_audit.run(args)

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertIn("Host process audit unavailable", payload["errors"][0])

    @mock.patch("dev.scripts.devctl.commands.process_audit.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_audit.scan_repo_hygiene_process_tree"
    )
    def test_run_strict_warns_but_does_not_fail_for_recent_repo_tooling_processes(
        self,
        scan_mock,
        write_output_mock,
    ) -> None:
        scan_mock.return_value = (
            [
                {
                    "pid": 210,
                    "ppid": 99,
                    "etime": "05:00",
                    "elapsed_seconds": 300,
                    "command": "/bin/zsh -c python3 dev/scripts/devctl.py docs-check --strict-tooling",
                    "match_source": "direct",
                    "match_scope": "repo_tooling",
                },
                {
                    "pid": 211,
                    "ppid": 210,
                    "etime": "04:59",
                    "elapsed_seconds": 299,
                    "command": "/opt/homebrew/bin/qemu-system-riscv64",
                    "match_source": "descendant",
                    "match_scope": "repo_tooling",
                },
            ],
            [],
        )
        args = build_parser().parse_args(["process-audit", "--strict", "--format", "json"])

        rc = process_audit.run(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["active_recent_advisory_count"], 2)
        self.assertIn("Active repo-tooling host processes", payload["warnings"][0])

    @mock.patch("dev.scripts.devctl.commands.process_audit.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_audit.scan_repo_hygiene_process_tree"
    )
    def test_run_strict_fails_for_recent_repo_runtime_processes(
        self,
        scan_mock,
        write_output_mock,
    ) -> None:
        scan_mock.return_value = (
            [
                {
                    "pid": 410,
                    "ppid": 99,
                    "etime": "05:00",
                    "elapsed_seconds": 300,
                    "command": "cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture",
                    "match_source": "direct",
                    "match_scope": "repo_runtime",
                },
                {
                    "pid": 411,
                    "ppid": 410,
                    "etime": "04:59",
                    "elapsed_seconds": 299,
                    "command": "/Users/jguida941/testing_upgrade/codex-voice/rust/target/debug/deps/codex_voice-deadbeef --nocapture",
                    "match_source": "descendant",
                    "match_scope": "repo_runtime",
                },
            ],
            [],
        )
        args = build_parser().parse_args(
            ["process-audit", "--strict", "--format", "json"]
        )

        rc = process_audit.run(args)

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["active_recent_blocking_count"], 2)
        self.assertIn(
            "Active runtime/test repo-related host processes",
            payload["errors"][0],
        )

    @mock.patch("dev.scripts.devctl.commands.process_audit.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_audit.scan_repo_hygiene_process_tree"
    )
    def test_run_strict_fails_for_recent_detached_repo_tooling_processes(
        self,
        scan_mock,
        write_output_mock,
    ) -> None:
        scan_mock.return_value = (
            [
                {
                    "pid": 510,
                    "ppid": 1,
                    "etime": "00:10",
                    "elapsed_seconds": 10,
                    "command": "python3 -c import time; time.sleep(300)",
                    "match_source": "direct",
                    "match_scope": "repo_tooling",
                }
            ],
            [],
        )
        args = build_parser().parse_args(
            ["process-audit", "--strict", "--format", "json"]
        )

        rc = process_audit.run(args)

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["recent_detached_count"], 1)
        self.assertEqual(payload["active_recent_advisory_count"], 0)
        self.assertIn(
            "Recently detached repo-related host processes detected",
            payload["errors"][0],
        )
