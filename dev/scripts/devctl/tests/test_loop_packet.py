"""Tests for `devctl loop-packet` parser and command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import loop_packet


def _base_args(**overrides):
    payload = {
        "source_json": [],
        "prefer_source": "triage-loop",
        "max_age_hours": 72.0,
        "max_draft_chars": 1600,
        "allow_auto_send": False,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


class LoopPacketParserTests(unittest.TestCase):
    def test_cli_accepts_loop_packet_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "loop-packet",
                "--source-json",
                "/tmp/source.json",
                "--prefer-source",
                "mutation-loop",
                "--max-age-hours",
                "24",
                "--max-draft-chars",
                "1200",
                "--allow-auto-send",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "loop-packet")
        self.assertEqual(args.source_json, ["/tmp/source.json"])
        self.assertEqual(args.prefer_source, "mutation-loop")
        self.assertEqual(args.max_age_hours, 24.0)
        self.assertEqual(args.max_draft_chars, 1200)
        self.assertTrue(args.allow_auto_send)
        self.assertEqual(args.format, "json")


class LoopPacketCommandTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.loop_packet.write_output")
    def test_builds_packet_from_triage_loop_source(self, write_output_mock) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "coderabbit-ralph-loop.json"
            source_path.write_text(
                json.dumps(
                    {
                        "command": "triage-loop",
                        "timestamp": datetime.now(timezone.utc)
                        .isoformat()
                        .replace("+00:00", "Z"),
                        "branch": "develop",
                        "reason": "report_only_below_threshold",
                        "unresolved_count": 3,
                    }
                ),
                encoding="utf-8",
            )
            args = _base_args(source_json=[str(source_path)])
            rc = loop_packet.run(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["source_command"], "triage-loop")
        self.assertEqual(payload["risk"], "medium")
        self.assertFalse(payload["terminal_packet"]["auto_send"])
        self.assertIn("Loop feedback packet", payload["terminal_packet"]["draft_text"])

    @patch("dev.scripts.devctl.commands.loop_packet.write_output")
    def test_allow_auto_send_only_when_low_risk_source_is_eligible(
        self, write_output_mock
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "coderabbit-ralph-loop.json"
            source_path.write_text(
                json.dumps(
                    {
                        "command": "triage-loop",
                        "timestamp": datetime.now(timezone.utc)
                        .isoformat()
                        .replace("+00:00", "Z"),
                        "branch": "develop",
                        "reason": "resolved",
                        "unresolved_count": 0,
                    }
                ),
                encoding="utf-8",
            )
            args = _base_args(source_json=[str(source_path)], allow_auto_send=True)
            rc = loop_packet.run(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["terminal_packet"]["auto_send"])

    @patch("dev.scripts.devctl.commands.loop_packet.write_output")
    def test_stale_source_fails_guard(self, write_output_mock) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "mutation-ralph-loop.json"
            source_path.write_text(
                json.dumps(
                    {
                        "command": "mutation-loop",
                        "timestamp": (
                            datetime.now(timezone.utc) - timedelta(hours=200)
                        )
                        .isoformat()
                        .replace("+00:00", "Z"),
                        "reason": "report_only_below_threshold",
                        "last_score": 0.55,
                        "threshold": 0.8,
                    }
                ),
                encoding="utf-8",
            )
            args = _base_args(source_json=[str(source_path)], max_age_hours=24.0)
            rc = loop_packet.run(args)

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["reason"], "source_stale")

    @patch("dev.scripts.devctl.commands.loop_packet.write_output")
    @patch("dev.scripts.devctl.commands.loop_packet._build_live_triage_source")
    def test_falls_back_to_live_triage_source_when_artifacts_missing(
        self, fallback_mock, write_output_mock
    ) -> None:
        fallback_mock.return_value = {
            "path": "<generated:live-triage>",
            "command": "triage",
            "payload": {
                "command": "triage",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "rollup": {"total": 0, "by_severity": {"high": 0, "medium": 0}},
                "next_actions": ["No urgent triage actions detected from current signals."],
            },
            "timestamp": datetime.now(timezone.utc),
            "mtime": datetime.now(timezone.utc).timestamp(),
        }
        args = _base_args(source_json=["/tmp/does-not-exist-feedback-loop-source.json"])
        rc = loop_packet.run(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["source_path"], "<generated:live-triage>")
        self.assertEqual(payload["source_command"], "triage")
        self.assertTrue(any("no artifact source found" in row for row in payload["warnings"]))


if __name__ == "__main__":
    unittest.main()
