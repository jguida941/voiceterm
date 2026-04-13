"""Tests for the dogfood reporting command."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.cli import COMMAND_HANDLERS, READ_ONLY_COMMANDS, build_parser
from dev.scripts.devctl.commands.listing import COMMANDS
from dev.scripts.devctl.commands.reporting import dogfood as command


class DogfoodParserTests(unittest.TestCase):
    def test_parser_accepts_record_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "dogfood",
                "--record",
                "--dev-mode",
                "--target-kind",
                "command",
                "--target-id",
                "dogfood",
                "--status",
                "passed",
                "--actor",
                "codex",
                "--provider",
                "codex",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "dogfood")
        self.assertTrue(args.record)
        self.assertTrue(args.dev_mode)
        self.assertEqual(args.target_kind, "command")
        self.assertEqual(args.target_id, "dogfood")
        self.assertEqual(args.status, "passed")
        self.assertEqual(args.actor, "codex")
        self.assertEqual(args.provider, "codex")

    def test_handler_and_listing_registered(self) -> None:
        self.assertIn("dogfood", COMMAND_HANDLERS)
        self.assertIn("dogfood", COMMANDS)
        self.assertNotIn("dogfood", READ_ONLY_COMMANDS)
        self.assertIs(COMMAND_HANDLERS["dogfood"], command.run)


class DogfoodCommandTests(unittest.TestCase):
    def test_record_requires_explicit_dev_mode(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "dogfood",
                "--record",
                "--target-kind",
                "command",
                "--target-id",
                "dogfood",
                "--status",
                "passed",
                "--format",
                "json",
            ]
        )

        self.assertEqual(command.run(args), 2)

    def test_record_writes_log_and_summary_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            log_path = root / "dogfood.jsonl"
            summary_root = root / "summary"
            output_path = root / "dogfood-output.json"
            parser = build_parser()
            args = parser.parse_args(
                [
                    "dogfood",
                    "--record",
                    "--dev-mode",
                    "--log-path",
                    str(log_path),
                    "--summary-root",
                    str(summary_root),
                    "--target-kind",
                    "command",
                    "--target-id",
                    "dogfood",
                    "--status",
                    "passed",
                    "--actor",
                    "codex",
                    "--provider",
                    "codex",
                    "--output",
                    str(output_path),
                    "--format",
                    "json",
                ]
            )

            self.assertEqual(command.run(args), 0)

            recorded_rows = [
                json.loads(line)
                for line in log_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(recorded_rows), 1)
            self.assertEqual(recorded_rows[0]["target_kind"], "command")
            self.assertEqual(recorded_rows[0]["target_id"], "dogfood")
            self.assertEqual(recorded_rows[0]["status"], "passed")

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["command"], "dogfood")
            self.assertEqual(payload["recorded"]["target_id"], "dogfood")

            summary_json = summary_root / "summary.json"
            summary_md = summary_root / "summary.md"
            self.assertTrue(summary_json.is_file())
            self.assertTrue(summary_md.is_file())
            summary_payload = json.loads(summary_json.read_text(encoding="utf-8"))
            command_bucket = next(
                bucket
                for bucket in summary_payload["coverage"]
                if bucket["target_kind"] == "command"
            )
            self.assertGreaterEqual(command_bucket["catalog_total"], 1)
            self.assertEqual(command_bucket["covered_total"], 1)
            self.assertEqual(command_bucket["passed_total"], 1)

    def test_report_reads_existing_log_without_recording(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            log_path = root / "dogfood.jsonl"
            summary_root = root / "summary"
            output_path = root / "dogfood-output.md"
            parser = build_parser()

            first_args = parser.parse_args(
                [
                    "dogfood",
                    "--record",
                    "--dev-mode",
                    "--log-path",
                    str(log_path),
                    "--summary-root",
                    str(summary_root),
                    "--target-kind",
                    "role",
                    "--target-id",
                    "reviewer",
                    "--status",
                    "passed",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(command.run(first_args), 0)

            report_args = parser.parse_args(
                [
                    "dogfood",
                    "--report",
                    "--log-path",
                    str(log_path),
                    "--summary-root",
                    str(summary_root),
                    "--output",
                    str(output_path),
                    "--format",
                    "md",
                ]
            )
            self.assertEqual(command.run(report_args), 0)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("## Coverage", rendered)
            self.assertIn("`role` uncovered", rendered)
