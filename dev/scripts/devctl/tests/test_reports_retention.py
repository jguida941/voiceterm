"""Tests for reports-retention safety contracts."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from dev.scripts.devctl import reports_retention


class ReportsRetentionSafetyTests(TestCase):
    def test_resolve_reports_root_rejects_repo_root_and_git_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            (repo_root / ".git").mkdir()

            resolved_root, root_error = reports_retention.resolve_reports_root(
                repo_root, "."
            )
            self.assertIsNone(resolved_root)
            self.assertIn("repository root", root_error or "")

            resolved_git, git_error = reports_retention.resolve_reports_root(
                repo_root, ".git"
            )
            self.assertIsNone(resolved_git)
            self.assertIn(".git", git_error or "")

    def test_reports_plan_scans_only_managed_subroots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            protected = repo_root / "dev/reports/autonomy/queue"
            protected.mkdir(parents=True)
            (protected / "latest.json").write_text("{}", encoding="utf-8")

            plan = reports_retention.build_reports_cleanup_plan(
                repo_root,
                reports_root_arg="dev/reports",
                max_age_days=0,
                keep_recent=0,
            )

        self.assertTrue(plan["ok"])
        self.assertEqual(plan["candidate_count"], 0)
        managed_subroots = {item["subroot"] for item in plan["subroots"]}
        self.assertNotIn("autonomy/queue", managed_subroots)
