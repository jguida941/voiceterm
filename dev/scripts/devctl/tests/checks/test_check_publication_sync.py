"""Tests for check_publication_sync guard script."""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from unittest.mock import patch

from dev.scripts.devctl.tests.conftest import load_repo_module


class CheckPublicationSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_repo_module(
            "check_publication_sync",
            "dev/scripts/checks/publication_sync_guard/command.py",
        )

    def test_main_fails_when_publication_is_stale(self) -> None:
        payload = {
            "ok": False,
            "registry_path": "dev/config/publication_sync_registry.json",
            "head_ref": "HEAD",
            "resolved_head_ref": "abc123",
            "publication_filter": None,
            "publication_count": 1,
            "stale_publication_count": 1,
            "error_count": 0,
            "errors": [],
            "publications": [
                {
                    "id": "paper-site",
                    "stale": True,
                    "impacted_path_count": 1,
                    "impacted_paths": ["AGENTS.md"],
                    "errors": [],
                }
            ],
        }
        stdout = io.StringIO()
        argv = [
            "check_publication_sync.py",
            "--format",
            "text",
        ]
        with patch.object(self.script, "build_publication_sync_report", return_value=payload):
            with patch.object(sys, "argv", argv):
                with contextlib.redirect_stdout(stdout):
                    rc = self.script.main()

        self.assertEqual(rc, 1)
        self.assertIn("stale_publications: 1", stdout.getvalue())

    def test_main_report_only_succeeds(self) -> None:
        payload = {
            "ok": False,
            "registry_path": "dev/config/publication_sync_registry.json",
            "head_ref": "HEAD",
            "resolved_head_ref": "abc123",
            "publication_filter": None,
            "publication_count": 1,
            "stale_publication_count": 1,
            "error_count": 0,
            "errors": [],
            "publications": [
                {
                    "id": "paper-site",
                    "stale": True,
                    "impacted_path_count": 1,
                    "impacted_paths": ["AGENTS.md"],
                    "errors": [],
                }
            ],
        }
        stdout = io.StringIO()
        argv = [
            "check_publication_sync.py",
            "--report-only",
            "--format",
            "json",
        ]
        with patch.object(self.script, "build_publication_sync_report", return_value=payload):
            with patch.object(sys, "argv", argv):
                with contextlib.redirect_stdout(stdout):
                    rc = self.script.main()

        self.assertEqual(rc, 0)
        self.assertIn('"stale_publication_count": 1', stdout.getvalue())

    def test_main_release_branch_aware_allows_stale_feature_branch(self) -> None:
        payload = {
            "ok": False,
            "registry_path": "dev/config/publication_sync_registry.json",
            "head_ref": "HEAD",
            "resolved_head_ref": "abc123",
            "publication_filter": None,
            "publication_count": 1,
            "stale_publication_count": 1,
            "error_count": 0,
            "errors": [],
            "publications": [
                {
                    "id": "paper-site",
                    "stale": True,
                    "impacted_path_count": 1,
                    "impacted_paths": ["AGENTS.md"],
                    "errors": [],
                }
            ],
        }
        stdout = io.StringIO()
        argv = [
            "check_publication_sync.py",
            "--release-branch-aware",
            "--format",
            "text",
        ]
        with patch.object(
            self.script,
            "build_publication_sync_report",
            return_value=payload,
        ):
            with patch.object(
                self.script,
                "load_push_policy",
                return_value=type("Policy", (), {"release_branch": "master"})(),
            ):
                with patch.object(
                    self.script,
                    "head_matches_release_branch",
                    return_value=False,
                ):
                    with patch.object(sys, "argv", argv):
                        with contextlib.redirect_stdout(stdout):
                            rc = self.script.main()

        self.assertEqual(rc, 0)
        self.assertIn("blocking_ok: True", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
