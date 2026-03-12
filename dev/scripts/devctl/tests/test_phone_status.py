"""Tests for devctl phone-status parser and command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl import phone_status_views
from dev.scripts.devctl.autonomy.phone_status import build_phone_status
from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import phone_status


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "phone_json": "dev/reports/autonomy/queue/phone/latest.json",
        "view": "compact",
        "emit_projections": None,
        "format": "json",
        "output": None,
        "json_output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _sample_payload() -> dict[str, object]:
    return {
        "command": "autonomy-phone-status",
        "phase": "paused",
        "reason": "max_tasks_reached",
        "controller": {
            "plan_id": "mp340",
            "controller_run_id": "abc123",
            "branch_base": "develop",
            "mode_effective": "report-only",
            "resolved": False,
            "rounds_completed": 2,
            "max_rounds": 6,
            "tasks_completed": 4,
            "max_tasks": 4,
            "latest_working_branch": "feature/autoloop-r2",
        },
        "loop": {
            "unresolved_count": 3,
            "risk": "high",
            "next_actions": ["Run report-only", "Escalate to review"],
        },
        "terminal": {
            "trace": ["attempt=1", "attempt=2"],
            "draft_text": "patch candidate",
            "auto_send": False,
        },
        "source_run": {
            "run_id": 111,
            "run_sha": "deadbeef",
            "run_url": "https://example.invalid/runs/111",
        },
        "ralph": {
            "available": True,
            "phase": "triage",
            "attempt": 1,
            "max_attempts": 3,
            "fix_rate_pct": 66.7,
            "fixed_count": 2,
            "total_findings": 3,
            "unresolved_count": 1,
            "branch": "develop",
            "last_run": "2026-03-11T12:00:00Z",
        },
        "warnings": [],
        "errors": [],
    }


class PhoneStatusParserTests(unittest.TestCase):
    def test_cli_accepts_phone_status_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "phone-status",
                "--phone-json",
                "/tmp/phone.json",
                "--view",
                "trace",
                "--emit-projections",
                "/tmp/projections",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "phone-status")
        self.assertEqual(args.phone_json, "/tmp/phone.json")
        self.assertEqual(args.view, "trace")
        self.assertEqual(args.emit_projections, "/tmp/projections")
        self.assertEqual(args.format, "json")


class PhoneStatusCommandTests(unittest.TestCase):
    def test_build_phone_status_loads_ralph_report_and_latest_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            report_path = (
                repo_root
                / "dev"
                / "reports"
                / "ralph"
                / "latest"
                / "ralph-report.json"
            )
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(
                    {
                        "phase": "triage",
                        "attempt": 2,
                        "max_attempts": 5,
                        "total_findings": 4,
                        "fixed_count": 3,
                        "unresolved_count": 1,
                        "branch": "feature/ralph",
                        "last_run": "2026-03-12T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )

            payload = build_phone_status(
                plan_id="MP-376",
                controller_run_id="run-42",
                repo="voiceterm",
                branch_base="develop",
                mode_effective="report-only",
                reason="review_follow_up_required",
                resolved=False,
                rounds_completed=2,
                tasks_completed=3,
                max_rounds=5,
                max_tasks=8,
                current_round=2,
                latest_working_branch="feature/governance-quality-sweep",
                triage_report={
                    "reason": "needs_review",
                    "unresolved_count": 2,
                    "attempts": [
                        {"run_id": 11, "status": "queued"},
                        {"run_id": 12, "run_sha": "deadbeef", "status": "failed"},
                    ],
                },
                loop_packet_report={
                    "next_actions": ["Refresh bridge", "Send fix slice"],
                    "terminal_packet": {
                        "draft_text": "candidate patch",
                        "auto_send": False,
                    },
                },
                checkpoint_packet={
                    "terminal_trace": ["step 1", "", "step 2", "step 3"],
                },
                warnings=[],
                errors=[],
                max_draft_chars=80,
                max_trace_lines=2,
                repo_root=repo_root,
            )

            self.assertEqual(payload["source_run"]["run_id"], 12)
            self.assertEqual(payload["terminal"]["trace"], ["step 1", "step 2"])
            self.assertEqual(payload["ralph"]["phase"], "triage")
            self.assertEqual(payload["ralph"]["fix_rate_pct"], 75.0)
            self.assertTrue(payload["ralph"]["available"])

    def test_view_payload_falls_back_to_compact_projection(self) -> None:
        payload = _sample_payload()

        projection = phone_status_views.view_payload(payload, "unexpected-view")

        self.assertEqual(projection["view"], "compact")
        self.assertEqual(projection["plan_id"], "mp340")
        self.assertEqual(projection["ralph_phase"], "triage")
        self.assertEqual(
            projection["next_actions"],
            ["Run report-only", "Escalate to review"],
        )

    def test_render_report_markdown_renders_trace_projection(self) -> None:
        payload = _sample_payload()
        report = {
            "ok": True,
            "input_path": "/tmp/phone.json",
            "view": "trace",
            "timestamp": "2026-03-11T12:00:00Z",
            "projection_dir": None,
            "warnings": [],
            "errors": [],
            "ralph": payload["ralph"],
            "view_payload": phone_status_views.view_payload(payload, "trace"),
        }

        output = phone_status_views.render_report_markdown(report)

        self.assertIn("## Trace View", output)
        self.assertIn("- controller_run_id: abc123", output)
        self.assertIn("- attempt=1", output)
        self.assertIn("patch candidate", output)

    def test_command_writes_projection_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            input_json = root / "latest.json"
            output_json = root / "report.json"
            projection_dir = root / "controller-state"
            input_json.write_text(json.dumps(_sample_payload()), encoding="utf-8")

            args = make_args(
                phone_json=str(input_json),
                view="actions",
                emit_projections=str(projection_dir),
                output=str(output_json),
            )
            rc = phone_status.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["view"], "actions")
            self.assertEqual(payload["view_payload"]["reason"], "max_tasks_reached")
            projection_files = payload.get("projection_files", {})
            for key in (
                "full_json",
                "compact_json",
                "trace_ndjson",
                "actions_json",
                "latest_md",
            ):
                self.assertIn(key, projection_files)
                self.assertTrue(Path(projection_files[key]).exists())

            trace_lines = Path(projection_files["trace_ndjson"]).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(trace_lines), 2)

    def test_command_fails_when_input_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output_json = root / "report.json"
            args = make_args(
                phone_json=str(root / "missing.json"),
                output=str(output_json),
            )
            rc = phone_status.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertTrue(any("phone status artifact not found" in row for row in payload.get("errors", [])))


if __name__ == "__main__":
    unittest.main()
