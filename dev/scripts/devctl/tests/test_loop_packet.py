"""Tests for `devctl loop-packet` parser and command behavior."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import loop_packet
from dev.scripts.devctl.commands.loop_packet_helpers import (
    ArtifactSourceRow,
    _build_live_triage_source,
)


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
    @patch("dev.scripts.devctl.commands.packets.loop_packet_sources.build_next_actions")
    @patch("dev.scripts.devctl.commands.packets.loop_packet_sources.build_issue_rollup")
    @patch("dev.scripts.devctl.commands.packets.loop_packet_sources.classify_issues")
    @patch("dev.scripts.devctl.commands.packets.loop_packet_sources.build_project_report")
    def test_live_triage_source_includes_probe_report(
        self,
        build_report_mock,
        classify_issues_mock,
        build_issue_rollup_mock,
        build_next_actions_mock,
    ) -> None:
        build_report_mock.return_value = {"git": {"changes": []}, "mutants": {"results": {}}}
        classify_issues_mock.return_value = []
        build_issue_rollup_mock.return_value = {"total": 0, "by_severity": {}}
        build_next_actions_mock.return_value = ["No urgent triage actions detected from current signals."]

        source = _build_live_triage_source()

        self.assertEqual(source.command, "triage")
        call_kwargs = build_report_mock.call_args.kwargs
        self.assertTrue(call_kwargs["include_probe_report"])

    def test_builds_packet_from_triage_loop_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "coderabbit-ralph-loop.json"
            output_path = Path(tmp_dir) / "packet.json"
            source_path.write_text(
                json.dumps(
                    {
                        "command": "triage-loop",
                        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "branch": "develop",
                        "reason": "report_only_below_threshold",
                        "unresolved_count": 3,
                    }
                ),
                encoding="utf-8",
            )
            args = _base_args(source_json=[str(source_path)], output=str(output_path))
            rc = loop_packet.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["source_command"], "triage-loop")
        self.assertEqual(payload["risk"], "medium")
        self.assertFalse(payload["terminal_packet"]["auto_send"])
        self.assertIn("Loop feedback packet", payload["terminal_packet"]["draft_text"])

    def test_triage_loop_routes_probe_guidance_into_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            source_path = tmp_root / "coderabbit-ralph-loop.json"
            output_path = tmp_root / "packet.json"
            report_root = tmp_root / "probes"
            report_root.mkdir(parents=True, exist_ok=True)
            source_path.write_text(
                json.dumps(
                    {
                        "command": "triage-loop",
                        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "branch": "develop",
                        "reason": "no fix command configured",
                        "unresolved_count": 2,
                        "backlog_items": [
                            {
                                "severity": "high",
                                "category": "python",
                                "summary": "dev/scripts/devctl/auth.py:12 - Auth flow and retry loop are coupled.",
                                "file_path": "dev/scripts/devctl/auth.py",
                                "line": 12,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (report_root / "review_targets.json").write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "file_path": "dev/scripts/devctl/auth.py",
                                "check_id": "probe_side_effect_mixing",
                                "severity": "high",
                                "line": 10,
                                "end_line": 14,
                                "ai_instruction": "Split the auth validator from the retry orchestration before editing the caller.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            args = _base_args(source_json=[str(source_path)], output=str(output_path))
            with patch.dict(os.environ, {"DEVCTL_PROBE_REPORT_ROOT": str(report_root)}, clear=False):
                rc = loop_packet.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(payload["source_command"], "triage-loop")
        self.assertEqual(len(payload["probe_guidance"]), 1)
        self.assertIn(
            "Split the auth validator from the retry orchestration before editing the caller.",
            payload["terminal_packet"]["draft_text"],
        )
        self.assertEqual(payload["terminal_packet"]["probe_guidance_count"], 1)
        self.assertTrue(payload["terminal_packet"]["guidance_adoption_required"])
        self.assertTrue(payload["guidance_contract"]["guidance_adoption_required"])
        self.assertIn(
            "default repair plan unless you can justify waiving it",
            payload["terminal_packet"]["draft_text"],
        )

    def test_allow_auto_send_only_when_low_risk_source_is_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "coderabbit-ralph-loop.json"
            output_path = Path(tmp_dir) / "packet.json"
            source_path.write_text(
                json.dumps(
                    {
                        "command": "triage-loop",
                        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "branch": "develop",
                        "reason": "resolved",
                        "unresolved_count": 0,
                    }
                ),
                encoding="utf-8",
            )
            args = _base_args(
                source_json=[str(source_path)],
                allow_auto_send=True,
                output=str(output_path),
            )
            rc = loop_packet.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["terminal_packet"]["auto_send"])

    def test_decision_mode_blocks_auto_send_and_surfaces_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            source_path = tmp_root / "coderabbit-ralph-loop.json"
            output_path = tmp_root / "packet.json"
            report_root = tmp_root / "probes"
            latest = report_root / "latest"
            latest.mkdir(parents=True, exist_ok=True)
            source_path.write_text(
                json.dumps(
                    {
                        "command": "triage-loop",
                        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "branch": "develop",
                        "reason": "resolved",
                        "unresolved_count": 0,
                        "backlog_items": [
                            {
                                "severity": "high",
                                "category": "python",
                                "summary": "dev/scripts/devctl/auth.py:12 - Auth flow needs approval.",
                                "file_path": "dev/scripts/devctl/auth.py",
                                "line": 12,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (report_root / "review_targets.json").write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "finding_id": "finding-approval",
                                "file_path": "dev/scripts/devctl/auth.py",
                                "symbol": "validate_auth",
                                "check_id": "probe_side_effect_mixing",
                                "severity": "high",
                                "line": 10,
                                "end_line": 14,
                                "ai_instruction": "Split the auth validator from the retry orchestration before editing the caller.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (latest / "summary.json").write_text(
                json.dumps(
                    {
                        "decision_packets": [
                            {
                                "finding_id": "finding-approval",
                                "file_path": "dev/scripts/devctl/auth.py",
                                "symbol": "validate_auth",
                                "check_id": "probe_side_effect_mixing",
                                "decision_mode": "approval_required",
                                "rationale": "Auth contract changes require approval.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            args = _base_args(
                source_json=[str(source_path)],
                allow_auto_send=True,
                output=str(output_path),
            )
            with patch.dict(os.environ, {"DEVCTL_PROBE_REPORT_ROOT": str(report_root)}, clear=False):
                rc = loop_packet.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertFalse(payload["terminal_packet"]["auto_send"])
        self.assertTrue(payload["guidance_contract"]["approval_required"])
        self.assertEqual(
            payload["guidance_contract"]["decision_modes"],
            ["approval_required"],
        )
        self.assertIn("decision_mode=approval_required", payload["terminal_packet"]["draft_text"])
        self.assertIn("request approval first", payload["terminal_packet"]["draft_text"])

    def test_stale_source_fails_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "mutation-ralph-loop.json"
            output_path = Path(tmp_dir) / "packet.json"
            source_path.write_text(
                json.dumps(
                    {
                        "command": "mutation-loop",
                        "timestamp": (datetime.now(UTC) - timedelta(hours=200)).isoformat().replace("+00:00", "Z"),
                        "reason": "report_only_below_threshold",
                        "last_score": 0.55,
                        "threshold": 0.8,
                    }
                ),
                encoding="utf-8",
            )
            args = _base_args(
                source_json=[str(source_path)],
                max_age_hours=24.0,
                output=str(output_path),
            )
            rc = loop_packet.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["reason"], "source_stale")

    @patch("dev.scripts.devctl.commands.loop_packet._build_live_triage_source")
    def test_falls_back_to_live_triage_source_when_artifacts_missing(self, fallback_mock) -> None:
        fallback_mock.return_value = ArtifactSourceRow(
            path="<generated:live-triage>",
            command="triage",
            payload={
                "command": "triage",
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "rollup": {"total": 0, "by_severity": {"high": 0, "medium": 0}},
                "next_actions": ["No urgent triage actions detected from current signals."],
            },
            timestamp=datetime.now(UTC),
            mtime=datetime.now(UTC).timestamp(),
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "packet.json"
            args = _base_args(
                source_json=["/tmp/does-not-exist-feedback-loop-source.json"],
                output=str(output_path),
            )
            rc = loop_packet.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["source_path"], "<generated:live-triage>")
        self.assertEqual(payload["source_command"], "triage")
        self.assertTrue(any("no artifact source found" in row for row in payload["warnings"]))

    @patch("dev.scripts.devctl.commands.packets.loop_packet_context.build_context_escalation_packet")
    def test_includes_context_packet_when_escalation_fires(self, escalation_mock) -> None:
        from dev.scripts.devctl.context_graph.escalation import ContextEscalationPacket

        escalation_mock.return_value = ContextEscalationPacket(
            trigger="loop-packet:triage-loop",
            query_terms=("check",),
            matched_nodes=1,
            edge_count=0,
            canonical_refs=("dev/scripts/devctl/cli.py",),
            evidence=("check: nodes=1, edges=0",),
            markdown=(
                "## Context Recovery Packet\n\n"
                "- Trigger: `loop-packet:triage-loop`\n"
                "- Query terms: `check`\n"
                "- Graph matches: nodes=1, edges=0\n"
                "- Canonical refs:\n"
                "  - `dev/scripts/devctl/cli.py`"
            ),
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "coderabbit-ralph-loop.json"
            output_path = Path(tmp_dir) / "packet.json"
            source_path.write_text(
                json.dumps(
                    {
                        "command": "triage-loop",
                        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "branch": "develop",
                        "reason": "report_only_below_threshold",
                        "unresolved_count": 1,
                        "next_actions": [
                            "Run `python3 dev/scripts/devctl.py check --profile ci`."
                        ],
                    }
                ),
                encoding="utf-8",
            )
            args = _base_args(source_json=[str(source_path)], output=str(output_path))
            rc = loop_packet.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertIn("context_packet", payload)
        self.assertEqual(payload["context_packet"]["trigger"], "loop-packet:triage-loop")
        self.assertIn("Context Recovery Packet", payload["terminal_packet"]["draft_text"])
        escalation_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
