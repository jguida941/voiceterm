"""Tests for devctl autonomy-report parser and command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import autonomy_report


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "source_root": "dev/reports/autonomy",
        "library_root": "dev/reports/autonomy/library",
        "run_label": None,
        "event_log": "dev/reports/audits/devctl_events.jsonl",
        "refresh_orchestrate": False,
        "copy_sources": True,
        "charts": False,
        "format": "json",
        "output": None,
        "json_output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class AutonomyReportParserTests(unittest.TestCase):
    def test_cli_accepts_autonomy_report_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "autonomy-report",
                "--source-root",
                "dev/reports/autonomy",
                "--library-root",
                "dev/reports/autonomy/library",
                "--run-label",
                "pilot-001",
                "--no-refresh-orchestrate",
                "--no-charts",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "autonomy-report")
        self.assertEqual(args.run_label, "pilot-001")
        self.assertFalse(args.refresh_orchestrate)
        self.assertFalse(args.charts)
        self.assertEqual(args.format, "json")


class AutonomyReportCommandTests(unittest.TestCase):
    def test_command_writes_bundle_with_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_root = root / "source"
            library_root = root / "library"
            output_json = root / "report.json"
            event_log = root / "events.jsonl"
            (source_root / "queue/phone").mkdir(parents=True, exist_ok=True)

            (source_root / "triage-loop-live.json").write_text(
                json.dumps(
                    {
                        "command": "triage-loop",
                        "ok": True,
                        "reason": "resolved",
                        "mode": "report-only",
                        "unresolved_count": 0,
                        "attempts": [{"attempt": 1}],
                    }
                ),
                encoding="utf-8",
            )
            (source_root / "mutation-loop-live.json").write_text(
                json.dumps(
                    {
                        "command": "mutation-loop",
                        "ok": True,
                        "reason": "threshold_met",
                        "last_score": 0.91,
                        "threshold": 0.80,
                    }
                ),
                encoding="utf-8",
            )
            (source_root / "autonomy-loop-live.json").write_text(
                json.dumps(
                    {
                        "command": "autonomy-loop",
                        "ok": True,
                        "resolved": True,
                        "reason": "resolved",
                        "rounds_completed": 2,
                        "tasks_completed": 2,
                        "rounds": [
                            {"round": 1, "unresolved_count": 2},
                            {"round": 2, "unresolved_count": 0},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (source_root / "orchestrate-status-end.json").write_text(
                json.dumps({"ok": True, "errors": [], "warnings": []}),
                encoding="utf-8",
            )
            (source_root / "orchestrate-watch-end.json").write_text(
                json.dumps(
                    {
                        "ok": True,
                        "errors": [],
                        "warnings": [],
                        "stale_agent_count": 1,
                        "overdue_instruction_ack_count": 0,
                    }
                ),
                encoding="utf-8",
            )
            (source_root / "queue/phone/latest.json").write_text(
                json.dumps(
                    {
                        "command": "autonomy-phone-status",
                        "reason": "max_tasks_reached",
                        "controller": {
                            "mode_effective": "report-only",
                            "rounds_completed": 2,
                            "tasks_completed": 2,
                        },
                        "terminal": {"trace": ["r1", "r2"]},
                    }
                ),
                encoding="utf-8",
            )
            event_log.write_text('{"step":"a"}\n{"step":"b"}\n', encoding="utf-8")

            args = make_args(
                source_root=str(source_root),
                library_root=str(library_root),
                run_label="demo-run",
                event_log=str(event_log),
                output=str(output_json),
            )
            rc = autonomy_report.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["run_label"], "demo-run")
            self.assertEqual(payload["metrics"]["triage_unresolved_count"], 0)
            self.assertEqual(payload["metrics"]["autonomy_rounds_completed"], 2)
            self.assertEqual(payload["metrics"]["phone_reason"], "max_tasks_reached")
            self.assertEqual(payload["metrics"]["event_count"], 2)
            summary_json = Path(payload["bundle_dir"]) / "summary.json"
            summary_md = Path(payload["bundle_dir"]) / "summary.md"
            self.assertTrue(summary_json.exists())
            self.assertTrue(summary_md.exists())
            self.assertIsNotNone(payload["sources"]["triage_loop"]["copied_path"])

    def test_command_fails_when_no_sources_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_root = root / "empty"
            library_root = root / "library"
            output_json = root / "report.json"
            source_root.mkdir(parents=True, exist_ok=True)

            args = make_args(
                source_root=str(source_root),
                library_root=str(library_root),
                run_label="missing",
                copy_sources=False,
                output=str(output_json),
            )
            rc = autonomy_report.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertTrue(
                any(
                    "no source artifacts found" in row
                    for row in payload.get("errors", [])
                )
            )


if __name__ == "__main__":
    unittest.main()
