"""Tests for `devctl reports-cleanup` command behavior."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import reports_cleanup


class ReportsCleanupParserTests(TestCase):
    def test_cli_accepts_reports_cleanup_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "reports-cleanup",
                "--dry-run",
                "--max-age-days",
                "45",
                "--keep-recent",
                "7",
                "--reports-root",
                "dev/reports",
            ]
        )
        self.assertEqual(args.command, "reports-cleanup")
        self.assertTrue(args.dry_run)
        self.assertEqual(args.max_age_days, 45)
        self.assertEqual(args.keep_recent, 7)
        self.assertEqual(args.reports_root, "dev/reports")


class ReportsCleanupCommandTests(TestCase):
    def _args(self, **overrides):
        base = {
            "reports_root": "dev/reports",
            "max_age_days": 30,
            "keep_recent": 1,
            "yes": True,
            "dry_run": True,
            "format": "json",
            "output": None,
            "pipe_command": None,
            "pipe_args": None,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @patch("dev.scripts.devctl.commands.reports_cleanup.write_output")
    def test_reports_cleanup_dry_run_keeps_directories(
        self,
        write_output_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            library = repo_root / "dev/reports/autonomy/library"
            old_dir = library / "old-run"
            fresh_dir = library / "fresh-run"
            old_dir.mkdir(parents=True)
            fresh_dir.mkdir(parents=True)
            (old_dir / "summary.md").write_text("old\n", encoding="utf-8")
            (fresh_dir / "summary.md").write_text("new\n", encoding="utf-8")

            old_ts = time.time() - (80 * 86400)
            fresh_ts = time.time() - (2 * 86400)
            os.utime(old_dir, (old_ts, old_ts))
            os.utime(fresh_dir, (fresh_ts, fresh_ts))

            args = self._args(dry_run=True, keep_recent=1, max_age_days=30)
            with patch("dev.scripts.devctl.commands.reports_cleanup.REPO_ROOT", repo_root):
                code = reports_cleanup.run(args)

            self.assertEqual(code, 0)
            payload = json.loads(write_output_mock.call_args.args[0])
            self.assertEqual(payload["candidate_count"], 1)
            self.assertEqual(payload["deleted_count"], 0)
            self.assertTrue(old_dir.exists())
            self.assertTrue(fresh_dir.exists())

    @patch("dev.scripts.devctl.commands.reports_cleanup.write_output")
    def test_reports_cleanup_deletes_only_stale_candidates(
        self,
        write_output_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            library = repo_root / "dev/reports/autonomy/library"
            old_a = library / "old-a"
            old_b = library / "old-b"
            fresh = library / "fresh"
            for directory in (old_a, old_b, fresh):
                directory.mkdir(parents=True)
                (directory / "artifact.txt").write_text("x\n", encoding="utf-8")

            old_a_ts = time.time() - (120 * 86400)
            old_b_ts = time.time() - (90 * 86400)
            fresh_ts = time.time() - (1 * 86400)
            os.utime(old_a, (old_a_ts, old_a_ts))
            os.utime(old_b, (old_b_ts, old_b_ts))
            os.utime(fresh, (fresh_ts, fresh_ts))

            args = self._args(dry_run=False, keep_recent=1, max_age_days=30, yes=True)
            with patch("dev.scripts.devctl.commands.reports_cleanup.REPO_ROOT", repo_root):
                code = reports_cleanup.run(args)

            self.assertEqual(code, 0)
            payload = json.loads(write_output_mock.call_args.args[0])
            self.assertEqual(payload["candidate_count"], 2)
            self.assertEqual(payload["deleted_count"], 2)
            self.assertFalse(old_a.exists())
            self.assertFalse(old_b.exists())
            self.assertTrue(fresh.exists())

    @patch("dev.scripts.devctl.commands.reports_cleanup.write_output")
    def test_reports_cleanup_rejects_reports_root_outside_repo(
        self,
        write_output_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            args = self._args(reports_root="/tmp", dry_run=True)

            with patch("dev.scripts.devctl.commands.reports_cleanup.REPO_ROOT", repo_root):
                code = reports_cleanup.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertTrue(
            any("outside repository root" in message for message in payload["errors"])
        )
