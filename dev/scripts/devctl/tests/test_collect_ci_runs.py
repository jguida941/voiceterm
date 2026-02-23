"""Tests for CI run collection helpers."""

from __future__ import annotations

import json
import subprocess
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl import collect


class CollectCiRunsTests(TestCase):
    @patch("dev.scripts.devctl.collect.shutil.which", return_value="/usr/bin/gh")
    @patch("dev.scripts.devctl.collect.subprocess.check_output")
    def test_collect_ci_runs_uses_extended_fields_when_available(
        self,
        check_output_mock,
        _which_mock,
    ) -> None:
        check_output_mock.return_value = json.dumps(
            [
                {
                    "displayTitle": "Rust TUI CI",
                    "name": "rust_ci.yml",
                    "event": "push",
                    "headBranch": "develop",
                    "headSha": "abc123",
                    "status": "completed",
                    "conclusion": "success",
                    "createdAt": "2026-02-23T10:00:00Z",
                    "updatedAt": "2026-02-23T10:03:00Z",
                    "url": "https://github.com/example/repo/actions/runs/1",
                    "databaseId": 1,
                }
            ]
        )

        report = collect.collect_ci_runs(5)
        self.assertIn("runs", report)
        self.assertNotIn("warning", report)
        self.assertEqual(report["runs"][0]["name"], "rust_ci.yml")
        self.assertEqual(report["runs"][0]["event"], "push")

    @patch("dev.scripts.devctl.collect.shutil.which", return_value="/usr/bin/gh")
    @patch("dev.scripts.devctl.collect.subprocess.check_output")
    def test_collect_ci_runs_falls_back_when_extended_fields_unavailable(
        self,
        check_output_mock,
        _which_mock,
    ) -> None:
        check_output_mock.side_effect = [
            subprocess.CalledProcessError(
                1,
                ["gh", "run", "list"],
                output="unknown json field: event\naccepts the following fields: ...",
            ),
            json.dumps(
                [
                    {
                        "displayTitle": "Rust TUI CI",
                        "headSha": "abc123",
                        "status": "completed",
                        "conclusion": "success",
                        "createdAt": "2026-02-23T10:00:00Z",
                        "updatedAt": "2026-02-23T10:03:00Z",
                    }
                ]
            ),
        ]

        report = collect.collect_ci_runs(5)
        self.assertIn("runs", report)
        self.assertIn("warning", report)
        run = report["runs"][0]
        self.assertEqual(run["name"], "Rust TUI CI")
        self.assertIsNone(run["event"])
        self.assertIsNone(run["headBranch"])
        self.assertIsNone(run["url"])
        self.assertIsNone(run["databaseId"])

    @patch("dev.scripts.devctl.collect.shutil.which", return_value="/usr/bin/gh")
    @patch("dev.scripts.devctl.collect.subprocess.check_output")
    def test_collect_ci_runs_does_not_retry_fallback_for_non_field_errors(
        self,
        check_output_mock,
        _which_mock,
    ) -> None:
        check_output_mock.side_effect = subprocess.CalledProcessError(
            1,
            ["gh", "run", "list"],
            output="error: authentication failed",
        )

        report = collect.collect_ci_runs(5)
        self.assertIn("error", report)
        self.assertIn("authentication failed", report["error"])
        self.assertEqual(check_output_mock.call_count, 1)
