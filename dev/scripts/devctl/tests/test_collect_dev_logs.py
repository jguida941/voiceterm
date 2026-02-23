"""Tests for dev-log collection helpers in devctl collect."""

import os
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl import collect


def _write_session(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class CollectDevLogsTests(unittest.TestCase):
    """Validate guarded Dev Mode JSONL summary collection."""

    def test_missing_sessions_dir_returns_zero_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dev"
            summary = collect.collect_dev_log_summary(dev_root=str(root), session_limit=3)
            self.assertFalse(summary["sessions_dir_exists"])
            self.assertEqual(summary["session_files_total"], 0)
            self.assertEqual(summary["events_scanned"], 0)
            self.assertEqual(summary["recent_sessions"], [])

    def test_collects_recent_sessions_and_aggregates_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dev"
            sessions_dir = root / "sessions"
            old_file = sessions_dir / "session-old.jsonl"
            new_file = sessions_dir / "session-new.jsonl"
            _write_session(
                old_file,
                [
                    '{"kind":"transcript","transcript_words":3,"latency_ms":120,"timestamp_unix_ms":1000}',
                    '{"kind":"empty","transcript_words":0,"timestamp_unix_ms":1100}',
                ],
            )
            _write_session(
                new_file,
                [
                    '{"kind":"error","transcript_words":0,"timestamp_unix_ms":1200}',
                    '{"kind":"transcript","transcript_words":5,"latency_ms":200,"timestamp_unix_ms":1300}',
                    "not-json",
                ],
            )
            os.utime(old_file, ns=(1_000_000_000, 1_000_000_000))
            os.utime(new_file, ns=(2_000_000_000, 2_000_000_000))

            summary = collect.collect_dev_log_summary(dev_root=str(root), session_limit=1)

            self.assertTrue(summary["sessions_dir_exists"])
            self.assertEqual(summary["session_files_total"], 2)
            self.assertEqual(summary["sessions_scanned"], 1)
            self.assertEqual(summary["events_scanned"], 3)
            self.assertEqual(summary["transcript_events"], 1)
            self.assertEqual(summary["empty_events"], 0)
            self.assertEqual(summary["error_events"], 1)
            self.assertEqual(summary["total_words"], 5)
            self.assertEqual(summary["avg_latency_ms"], 200)
            self.assertEqual(summary["parse_errors"], 1)
            self.assertEqual(len(summary["recent_sessions"]), 1)
            self.assertEqual(summary["recent_sessions"][0]["file"], "session-new.jsonl")


if __name__ == "__main__":
    unittest.main()
