"""Tests for `devctl process-watch` command behavior."""

from __future__ import annotations

import json
from unittest import TestCase, mock

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import process_watch


class ProcessWatchParserTests(TestCase):
    def test_cli_accepts_process_watch_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "process-watch",
                "--cleanup",
                "--strict",
                "--iterations",
                "3",
                "--interval-seconds",
                "2.5",
                "--stop-on-clean",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "process-watch")
        self.assertTrue(args.cleanup)
        self.assertTrue(args.strict)
        self.assertEqual(args.iterations, 3)
        self.assertEqual(args.interval_seconds, 2.5)
        self.assertTrue(args.stop_on_clean)
        self.assertEqual(args.format, "json")


class ProcessWatchCommandTests(TestCase):
    @mock.patch("dev.scripts.devctl.commands.process_watch.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_watch.build_process_audit_report"
    )
    @mock.patch(
        "dev.scripts.devctl.commands.process_watch.build_process_cleanup_report"
    )
    def test_run_handles_nonfatal_cleanup_errors_without_prefix_splitting(
        self,
        cleanup_mock,
        audit_mock,
        write_output_mock,
    ) -> None:
        cleanup_mock.return_value = {
            "cleanup_target_count": 0,
            "killed_count": 0,
            "warnings": [],
            "errors": ["plain cleanup failure"],
        }
        audit_mock.return_value = {
            "total_detected": 0,
            "orphaned_count": 0,
            "stale_active_count": 0,
            "active_recent_count": 0,
            "warnings": [],
            "errors": [],
            "ok": True,
        }
        args = build_parser().parse_args(
            [
                "process-watch",
                "--cleanup",
                "--iterations",
                "1",
                "--format",
                "json",
            ]
        )

        rc = process_watch.run(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["fatal_errors"], [])
        self.assertEqual(payload["errors"], ["iteration 1: plain cleanup failure"])

    @mock.patch("dev.scripts.devctl.commands.process_watch.write_output")
    @mock.patch("dev.scripts.devctl.commands.process_watch.time.sleep")
    @mock.patch(
        "dev.scripts.devctl.commands.process_watch.build_process_audit_report"
    )
    @mock.patch(
        "dev.scripts.devctl.commands.process_watch.build_process_cleanup_report"
    )
    def test_run_stops_early_when_clean(
        self,
        cleanup_mock,
        audit_mock,
        sleep_mock,
        write_output_mock,
    ) -> None:
        cleanup_mock.return_value = {
            "cleanup_target_count": 1,
            "killed_count": 1,
            "warnings": [],
            "errors": [],
        }
        audit_mock.return_value = {
            "total_detected": 0,
            "orphaned_count": 0,
            "stale_active_count": 0,
            "active_recent_count": 0,
            "warnings": [],
            "errors": [],
            "ok": True,
        }
        args = build_parser().parse_args(
            [
                "process-watch",
                "--cleanup",
                "--strict",
                "--iterations",
                "4",
                "--stop-on-clean",
                "--format",
                "json",
            ]
        )

        rc = process_watch.run(args)

        self.assertEqual(rc, 0)
        cleanup_mock.assert_called_once_with(dry_run=False, verify=False)
        audit_mock.assert_called_once_with(strict=True)
        sleep_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["iterations_run"], 1)
        self.assertEqual(payload["stop_reason"], "clean")
        self.assertTrue(payload["ok"])

    @mock.patch("dev.scripts.devctl.commands.process_watch.write_output")
    @mock.patch("dev.scripts.devctl.commands.process_watch.time.sleep")
    @mock.patch(
        "dev.scripts.devctl.commands.process_watch.build_process_audit_report"
    )
    def test_run_retries_until_iteration_cap_when_not_clean(
        self,
        audit_mock,
        sleep_mock,
        write_output_mock,
    ) -> None:
        audit_mock.side_effect = [
            {
                "total_detected": 2,
                "orphaned_count": 1,
                "stale_active_count": 1,
                "active_recent_count": 0,
                "warnings": [],
                "errors": ["orphaned"],
                "ok": False,
            },
            {
                "total_detected": 1,
                "orphaned_count": 0,
                "stale_active_count": 1,
                "active_recent_count": 0,
                "warnings": [],
                "errors": ["stale"],
                "ok": False,
            },
        ]
        args = build_parser().parse_args(
            [
                "process-watch",
                "--iterations",
                "2",
                "--interval-seconds",
                "1",
                "--format",
                "json",
            ]
        )

        rc = process_watch.run(args)

        self.assertEqual(rc, 1)
        self.assertEqual(audit_mock.call_count, 2)
        sleep_mock.assert_called_once_with(1.0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["iterations_run"], 2)
        self.assertEqual(payload["stop_reason"], "max_iterations_reached")
        self.assertFalse(payload["ok"])

    @mock.patch("dev.scripts.devctl.commands.process_watch.write_output")
    @mock.patch("dev.scripts.devctl.commands.process_watch.time.sleep")
    @mock.patch(
        "dev.scripts.devctl.commands.process_watch.build_process_audit_report"
    )
    @mock.patch(
        "dev.scripts.devctl.commands.process_watch.build_process_cleanup_report"
    )
    def test_run_returns_success_when_watch_recovers_to_clean_state(
        self,
        cleanup_mock,
        audit_mock,
        sleep_mock,
        write_output_mock,
    ) -> None:
        cleanup_mock.return_value = {
            "cleanup_target_count": 0,
            "killed_count": 0,
            "warnings": [],
            "errors": [],
        }
        audit_mock.side_effect = [
            {
                "total_detected": 1,
                "orphaned_count": 0,
                "stale_active_count": 0,
                "active_recent_count": 1,
                "warnings": [],
                "errors": ["Recently detached repo-related host processes detected"],
                "ok": False,
            },
            {
                "total_detected": 0,
                "orphaned_count": 0,
                "stale_active_count": 0,
                "active_recent_count": 0,
                "warnings": [],
                "errors": [],
                "ok": True,
            },
        ]
        args = build_parser().parse_args(
            [
                "process-watch",
                "--cleanup",
                "--strict",
                "--iterations",
                "4",
                "--interval-seconds",
                "1",
                "--stop-on-clean",
                "--format",
                "json",
            ]
        )

        rc = process_watch.run(args)

        self.assertEqual(rc, 0)
        self.assertEqual(cleanup_mock.call_count, 2)
        sleep_mock.assert_called_once_with(1.0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["iterations_run"], 2)
        self.assertEqual(payload["stop_reason"], "clean")
        self.assertTrue(payload["ok"])
