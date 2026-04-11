"""Tests for the devctl monitor command."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands import monitor
from dev.scripts.devctl.tests.runtime.test_monitor_snapshot import _sample_snapshot


class MonitorCommandTests(unittest.TestCase):
    def test_parser_accepts_follow_and_interval(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "monitor",
                "--mode",
                "remote_phone",
                "--agent",
                "codex",
                "--follow",
                "--interval",
                "3m",
                "--max-follow-snapshots",
                "2",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "monitor")
        self.assertEqual(args.mode, "remote_phone")
        self.assertEqual(args.agent, "codex")
        self.assertTrue(args.follow)
        self.assertEqual(args.interval, "3m")
        self.assertEqual(args.max_follow_snapshots, 2)

    def test_run_writes_single_pass_json_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "monitor.json"
            args = cli.build_parser().parse_args(
                [
                    "monitor",
                    "--format",
                    "json",
                    "--output",
                    str(output_path),
                ]
            )
            with patch(
                "dev.scripts.devctl.commands.monitor.build_monitor_snapshot",
                return_value=_sample_snapshot(),
            ):
                rc = monitor.run(args)

            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(payload["contract_id"], "MonitorSnapshot")
        self.assertEqual(payload["summary"]["state"], "active")

    def test_follow_requires_json_format(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "monitor",
                "--follow",
                "--format",
                "md",
            ]
        )
        with patch("sys.stderr.write") as stderr_write:
            rc = monitor.run(args)

        self.assertEqual(rc, 1)
        self.assertTrue(
            any("monitor --follow requires --format json" in call.args[0] for call in stderr_write.call_args_list)
        )

    def test_follow_appends_ndjson_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "monitor.ndjson"
            args = cli.build_parser().parse_args(
                [
                    "monitor",
                    "--follow",
                    "--format",
                    "json",
                    "--output",
                    str(output_path),
                    "--interval",
                    "1s",
                    "--max-follow-snapshots",
                    "2",
                ]
            )
            snapshots = [_sample_snapshot(), _sample_snapshot()]
            with (
                patch(
                    "dev.scripts.devctl.commands.monitor.build_monitor_snapshot",
                    side_effect=snapshots,
                ),
                patch("dev.scripts.devctl.commands.monitor.time.sleep", return_value=None),
            ):
                rc = monitor.run(args)

            lines = [
                json.loads(line)
                for line in output_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(rc, 0)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0]["follow"])
        self.assertEqual(lines[0]["snapshot_seq"], 0)
        self.assertEqual(lines[1]["snapshot_seq"], 1)


if __name__ == "__main__":
    unittest.main()
