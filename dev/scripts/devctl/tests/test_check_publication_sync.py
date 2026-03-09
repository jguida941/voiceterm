"""Tests for check_publication_sync guard script."""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from unittest.mock import patch

from conftest import load_repo_module


class CheckPublicationSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_repo_module(
            "check_publication_sync",
            "dev/scripts/checks/check_publication_sync.py",
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


if __name__ == "__main__":
    unittest.main()
