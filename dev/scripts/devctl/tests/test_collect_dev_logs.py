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
            summary = collect.collect_dev_log_summary(
                dev_root=str(root), session_limit=3
            )
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

            summary = collect.collect_dev_log_summary(
                dev_root=str(root), session_limit=1
            )

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
            self.assertEqual(
                summary["recent_sessions"][0]["file"], "session-new.jsonl"
            )

    def test_collects_session_averages_and_latest_event_iso(self) -> None:
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
                    '{"kind":"transcript","transcript_words":2,"latency_ms":0,"timestamp_unix_ms":1400}',
                    "[]",
                ],
            )
            os.utime(old_file, ns=(1_000_000_000, 1_000_000_000))
            os.utime(new_file, ns=(2_000_000_000, 2_000_000_000))

            summary = collect.collect_dev_log_summary(
                dev_root=str(root), session_limit=5
            )

            self.assertEqual(summary["sessions_scanned"], 2)
            self.assertEqual(summary["events_scanned"], 6)
            self.assertEqual(summary["transcript_events"], 3)
            self.assertEqual(summary["empty_events"], 1)
            self.assertEqual(summary["error_events"], 1)
            self.assertEqual(summary["total_words"], 10)
            self.assertEqual(summary["latency_samples"], 3)
            self.assertEqual(summary["avg_latency_ms"], 106)
            self.assertEqual(summary["parse_errors"], 1)
            self.assertEqual(
                summary["latest_event_iso"], "1970-01-01T00:00:01.400000+00:00"
            )
            self.assertEqual(
                [row["file"] for row in summary["recent_sessions"]],
                ["session-new.jsonl", "session-old.jsonl"],
            )
            self.assertEqual(summary["recent_sessions"][0]["avg_latency_ms"], 100)
            self.assertEqual(summary["recent_sessions"][0]["latency_samples"], 2)
            self.assertEqual(summary["recent_sessions"][0]["parse_errors"], 1)
            self.assertEqual(summary["recent_sessions"][1]["avg_latency_ms"], 120)
            self.assertEqual(summary["recent_sessions"][1]["latency_samples"], 1)


if __name__ == "__main__":
    unittest.main()
