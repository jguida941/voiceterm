"""Focused tests for review-channel watch lifecycle ownership."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.review_channel.watch_lifecycle import (
    claim_watch_lifecycle,
    release_watch_lifecycle,
    watch_state_path,
    write_watch_heartbeat,
    write_watch_stop,
)


class WatchLifecycleTests(unittest.TestCase):
    def test_state_file_is_rewritten_as_one_json_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_root = Path(tmpdir)
            owner, conflict = claim_watch_lifecycle(
                artifact_root=artifact_root,
                target="claude",
                status_filter="pending",
                started_at_utc="2026-04-14T15:00:00Z",
            )
            self.assertIsNotNone(owner)
            self.assertIsNone(conflict)
            assert owner is not None
            try:
                write_watch_heartbeat(
                    owner=owner,
                    snapshots_emitted=1,
                    heartbeat_utc="2026-04-14T15:00:02Z",
                )
                write_watch_stop(
                    owner=owner,
                    snapshots_emitted=1,
                    stop_reason="keyboard_interrupt",
                    stopped_at_utc="2026-04-14T15:00:03Z",
                )
            finally:
                release_watch_lifecycle(owner)

            payload = json.loads(
                watch_state_path(
                    artifact_root=artifact_root,
                    target="claude",
                    status_filter="pending",
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(payload["snapshots_emitted"], 1)
            self.assertEqual(payload["stop_reason"], "keyboard_interrupt")
            self.assertEqual(payload["last_heartbeat_utc"], "2026-04-14T15:00:03Z")


if __name__ == "__main__":
    unittest.main()
