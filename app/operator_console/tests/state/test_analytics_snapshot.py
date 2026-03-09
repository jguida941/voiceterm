from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.operator_console.state.analytics_snapshot import collect_repo_analytics


class AnalyticsSnapshotTests(unittest.TestCase):
    def test_collect_repo_analytics_fails_closed_for_other_repo_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot = collect_repo_analytics(Path(tmp_dir))

        self.assertEqual(snapshot.changed_files, 0)
        self.assertIn("only wired for the current codex-voice repo root", snapshot.collection_note or "")
