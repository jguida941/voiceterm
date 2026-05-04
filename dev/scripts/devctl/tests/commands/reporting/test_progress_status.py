"""Tests for the read-only progress-status command."""

from __future__ import annotations

import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands.reporting.progress_status import render_progress_markdown
from dev.scripts.devctl.runtime.stage_progress import (
    PROGRESS_ROOT_ENV,
    build_stage_progress_event,
    read_progress_snapshot,
    record_stage_progress_event,
)


class ProgressStatusCommandTests(unittest.TestCase):
    def test_progress_status_is_registered_read_only_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["progress-status", "--format", "json"])

        self.assertEqual(args.command, "progress-status")
        self.assertIn("progress-status", cli.READ_ONLY_COMMANDS)
        self.assertIs(cli.COMMAND_HANDLERS["progress-status"], cli.progress_status.run)

    def test_render_progress_markdown_includes_latest_event(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            with patch.dict(os.environ, {PROGRESS_ROOT_ENV: tmp_dir}, clear=False):
                record_stage_progress_event(
                    build_stage_progress_event(
                        command_name="guard",
                        phase="command.heartbeat",
                        status="running",
                        detail="still running",
                        elapsed_seconds=30,
                    )
                )
                payload = read_progress_snapshot(limit=5)

        markdown = render_progress_markdown(payload)
        self.assertIn("latest_status: `running`", markdown)
        self.assertIn("`command.heartbeat`", markdown)
        self.assertIn("still running", markdown)


if __name__ == "__main__":
    unittest.main()
