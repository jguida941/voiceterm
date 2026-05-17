"""Tests for typed devctl stage-progress artifacts."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from dev.scripts.devctl.runtime.stage_progress import (
    ARTIFACT_WRITES_ENV,
    PROGRESS_ROOT_ENV,
    StageProgressContext,
    build_stage_progress_event,
    read_progress_events,
    read_progress_snapshot,
    record_stage_progress_event,
)


class StageProgressTests(unittest.TestCase):
    def test_record_stage_progress_event_writes_latest_and_recent_tail(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            with patch.dict(os.environ, {PROGRESS_ROOT_ENV: tmp_dir}, clear=False):
                event = build_stage_progress_event(
                    command_name="check-router",
                    phase="command.heartbeat",
                    status="running",
                    detail="still running",
                    elapsed_seconds=12.3,
                    context=StageProgressContext(
                        child_pid=1234,
                        command=("python3", "dev/scripts/devctl.py", "check-router"),
                    ),
                )

                self.assertTrue(record_stage_progress_event(event))
                snapshot = read_progress_snapshot(limit=5)
                events = read_progress_events(limit=5)

        self.assertEqual(snapshot["latest"]["event_id"], event.event_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].command_name, "check-router")
        self.assertEqual(events[0].child_pid, 1234)

    def test_record_stage_progress_event_honors_artifact_suppression(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            with patch.dict(
                os.environ,
                {
                    PROGRESS_ROOT_ENV: tmp_dir,
                    ARTIFACT_WRITES_ENV: "1",
                },
                clear=False,
            ):
                event = build_stage_progress_event(
                    command_name="read-only",
                    phase="command.start",
                    status="started",
                )

                self.assertFalse(record_stage_progress_event(event))
                self.assertFalse((Path(tmp_dir) / "latest.json").exists())


if __name__ == "__main__":
    unittest.main()
