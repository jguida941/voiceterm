"""Tests for the devctl probe-report command."""

from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from dev.scripts.checks.probe_report.support import (
    AllowlistEntry,
    build_design_decision_packets,
)
from dev.scripts.checks.probe_report.contracts import (
    DECISION_PACKET_CONTRACT_ID,
    DECISION_PACKET_SCHEMA_VERSION,
    enrich_probe_hint_contract,
)
from dev.scripts.devctl import cli, quality_policy, review_probe_report
from dev.scripts.devctl.config import REPO_ROOT, get_repo_root
from dev.scripts.devctl.commands import probe_report
from dev.scripts.devctl.probe_topology import render_review_packet_markdown
from dev.scripts.devctl.quality_policy_loader import QUALITY_POLICY_ENV_VAR
from dev.scripts.devctl.quality_scan_mode import ADOPTION_BASE_REF, WORKTREE_HEAD_REF


def _probe_payload(
    command: str,
    *,
    file: str = "app/operator_console/state/watchdog_presenter.py",
    symbol: str = "watchdog_summary_line",
    severity: str = "medium",
    review_lens: str = "design_quality",
) -> dict:
    return {
        "command": command,
        "timestamp": "2026-03-10T04:00:00Z",
        "ok": True,
        "mode": "working-tree",
        "since_ref": None,
        "head_ref": "HEAD",
        "risk_hints": [
            {
                "file": file,
                "symbol": symbol,
                "risk_type": "design_smell",
                "severity": severity,
                "signals": ["sample signal"],
                "ai_instruction": "fix it",
                "review_lens": review_lens,
                "attach_docs": [],
            }
        ],
        "files_scanned": 3,
        "files_with_hints": 1,
    }


def _topology_payload() -> dict:
    return {
        "schema_version": 1,
        "contract_id": "FileTopology",
        "generated_at": "2026-03-10T04:00:00Z",
        "summary": {
            "source_files": 8,
            "edge_count": 12,
            "changed_files": 2,
            "changed_hint_files": 1,
            "focused_files": 2,
        },
        "changed_files": ["dev/scripts/devctl/commands/loop_packet.py"],
        "focused_files": [
            "app/operator_console/state/watchdog_presenter.py",
            "rust/src/bin/voiceterm/main.rs",
        ],
        "nodes": {},
        "edges": [],
        "hotspots": [
            {
                "file": "rust/src/bin/voiceterm/main.rs",
                "priority_score": 148,
                "hint_count": 1,
                "fan_in": 4,
                "fan_out": 6,
                "bridge_score": 4,
                "metric_explanations": {
                    "fan_in": "fan_in explanation",
                    "fan_out": "fan_out explanation",
                    "bridge_score": "bridge explanation",
                    "hotspot_rank": "rank explanation",
                },
                "changed": True,
                "owners": ["@jguida941"],
                "connected_files": [],
                "representative_hints": [
                    {
                        "probe": "probe_blank_line_frequency",
                        "symbol": "_metadata_from_snapshot",
                        "severity": "high",
                        "practice_title": "Add visual breaks between logical blocks",
                        "practice_explanation": "Blank lines make long functions easier to scan.",
                    }
                ],
                "bounded_next_slice": "fix the main render path",
            }
        ],
        "focused_graph": {"nodes": [], "edges": []},
        "warnings": [],
    }


def _review_packet_payload() -> dict:
    hotspot = _topology_payload()["hotspots"][0]
    return {
        "schema_version": 1,
        "contract_id": "ReviewPacket",
        "summary": {
            "risk_hints": 2,
            "files_with_hints": 2,
            "probe_count": 2,
            "top_hotspot": hotspot,
            "changed_hint_files": 1,
            "topology_edges": 12,
        },
        "hotspots": [hotspot],
        "focused_graph": {"nodes": [], "edges": []},
        "verification": {
            "probe_errors": [],
            "probe_warnings": [],
            "verified_by": ["devctl probe-report"],
        },
        "recommended_command": "python3 dev/scripts/devctl.py probe-report --format md",
    }


class ProbeReportCommandTests(unittest.TestCase):
    def test_build_design_decision_packets_defaults_mode_and_validation(self) -> None:
        raw_hint = _probe_payload("probe_design_smells")["risk_hints"][0]
        raw_hint["probe"] = "probe_design_smells"
        hint = enrich_probe_hint_contract(
            hint=raw_hint,
            repo_name="VoiceTerm",
        )
        packets = build_design_decision_packets(
            hints_by_file={hint["file"]: [hint]},
            allowlist=[
                AllowlistEntry(
                    file=hint["file"],
                    symbol=hint["symbol"],
                    probe="probe_design_smells",
                    disposition="design_decision",
                    reason="Keep the presenter boundary explicit while the state graph is still in flux.",
                    invariants=("Preserve the presenter/public contract.",),
                )
            ],
        )

        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0]["schema_version"], DECISION_PACKET_SCHEMA_VERSION)
        self.assertEqual(packets[0]["contract_id"], DECISION_PACKET_CONTRACT_ID)
        self.assertTrue(packets[0]["finding_id"])
        self.assertEqual(packets[0]["rule_id"], "probe_design_smells")
        self.assertEqual(packets[0]["decision_mode"], "recommend_only")
        self.assertEqual(
            packets[0]["invariants"],
            ["Preserve the presenter/public contract."],
        )
        self.assertTrue(packets[0]["rule_summary"])
        self.assertTrue(packets[0]["match_evidence"])
        self.assertTrue(packets[0]["rejected_rule_traces"])
        self.assertTrue(any("check --profile ci" in step for step in packets[0]["validation_plan"]))

    def test_build_design_decision_packets_match_probe_independently(self) -> None:
        raw_hint = _probe_payload("probe_design_smells")["risk_hints"][0]
        raw_hint["probe"] = "probe_design_smells"
        hint = enrich_probe_hint_contract(
            hint=raw_hint,
            repo_name="VoiceTerm",
        )
        packets = build_design_decision_packets(
            hints_by_file={hint["file"]: [hint]},
            allowlist=[
                AllowlistEntry(
                    file=hint["file"],
                    symbol=hint["symbol"],
                    probe="probe_identifier_density",
                    disposition="design_decision",
                    reason="wrong probe",
                )
            ],
        )

        self.assertEqual(packets, [])

    def test_render_probe_report_terminal_includes_top_hotspot(self) -> None:
        report = {
            "probe_results": [_probe_payload("probe_design_smells")],
            "review_packet": {"hotspots": _review_packet_payload()["hotspots"]},
            "decision_packets": [],
            "warnings": [],
            "errors": [],
        }

        output = review_probe_report.render_probe_report_terminal(report)

        self.assertIn("Top hotspot:", output)
        self.assertIn("rust/src/bin/voiceterm/main.rs", output)

    def test_render_probe_report_markdown_includes_decision_packets(self) -> None:
        report = {
            "ok": True,
            "mode": "working-tree",
            "summary": {"probe_count": 1},
            "probe_results": [_probe_payload("probe_design_smells")],
            "review_packet": _review_packet_payload(),
            "decision_packets": [
                {
                    "file": "dev/scripts/devctl/review_probe_report.py",
                    "symbol": "build_probe_report",
                    "probe": "probe_side_effect_mixing",
                    "severity": "medium",
                    "decision_mode": "recommend_only",
                    "rationale": "Keep the orchestration boundary visible while the packet contract settles.",
                }
            ],
            "warnings": [],
            "errors": [],
            "artifact_paths": {},
        }

        output = review_probe_report.render_probe_report_markdown(report)

        self.assertIn("## Design Decision Packets", output)
        self.assertIn("[recommend_only]", output)
        self.assertIn("build_probe_report", output)

    def test_render_probe_review_packet_markdown_includes_metric_and_practice_explanations(self) -> None:
        output = render_review_packet_markdown(
            _review_packet_payload(),
            rich_report_markdown="# probe report",
        )

        self.assertIn("fan_in_explanation", output)
        self.assertIn("practice: Add visual breaks between logical blocks", output)

    def test_run_aggregates_probe_results_and_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_root = Path(tmp_dir) / "probes"
            args = Namespace(
                since_ref=None,
                adoption_scan=False,
                head_ref="HEAD",
                quality_policy="/tmp/portable-policy.json",
                output_root=str(output_root),
                emit_artifacts=True,
                format="json",
                output=str(output_root / "command-output.json"),
                json_output=None,
                pipe_command=None,
                pipe_args=None,
            )

            payloads = [
                CompletedProcess(
                    ["python3"],
                    0,
                    stdout=json.dumps(_probe_payload("probe_design_smells")),
                    stderr="",
                ),
                CompletedProcess(
                    ["python3"],
                    0,
                    stdout=json.dumps(
                        _probe_payload(
                            "probe_clone_density",
                            file="rust/src/bin/voiceterm/main.rs",
                            symbol="render",
                            severity="high",
                            review_lens="ownership",
                        )
                    ),
                    stderr="",
                ),
            ]

            with (
                patch(
                    "dev.scripts.devctl.commands.probe_report.resolve_review_probe_script_ids",
                    return_value=("probe_design_smells", "probe_clone_density"),
                ) as mock_resolve_probe_ids,
                patch(
                    "dev.scripts.devctl.review_probe_report.subprocess.run",
                    side_effect=payloads,
                ),
                patch(
                    "dev.scripts.devctl.review_probe_report.build_probe_topology_artifact",
                    return_value=_topology_payload(),
                ),
                patch(
                    "dev.scripts.devctl.review_probe_report.build_review_packet",
                    return_value=_review_packet_payload(),
                ),
                patch(
                    "dev.scripts.devctl.review_probe_report.render_probe_report_markdown",
                    return_value="# probe report",
                ),
                patch(
                    "dev.scripts.devctl.review_probe_report.render_rich_report",
                    return_value="# rich report",
                ),
                patch(
                    "dev.scripts.devctl.commands.probe_report.render_probe_report_markdown",
                    return_value="# probe report",
                ),
                patch(
                    "dev.scripts.devctl.review_probe_report.resolve_quality_policy",
                    return_value=quality_policy.resolve_quality_policy(),
                ),
            ):
                rc = probe_report.run(args)

            mock_resolve_probe_ids.assert_called_once_with(
                repo_root=None,
                policy_path="/tmp/portable-policy.json",
            )

            self.assertEqual(rc, 0)
            summary_path = output_root / "latest" / "summary.json"
            review_targets_path = output_root / "review_targets.json"
            summary_md_path = output_root / "latest" / "summary.md"
            topology_path = output_root / "latest" / "file_topology.json"
            review_packet_json = output_root / "latest" / "review_packet.json"
            review_packet_md = output_root / "latest" / "review_packet.md"
            hotspots_mermaid = output_root / "latest" / "hotspots.mmd"
            hotspots_dot = output_root / "latest" / "hotspots.dot"
            self.assertTrue(summary_path.exists())
            self.assertTrue(review_targets_path.exists())
            self.assertTrue(summary_md_path.exists())
            self.assertTrue(topology_path.exists())
            self.assertTrue(review_packet_json.exists())
            self.assertTrue(review_packet_md.exists())
            self.assertTrue(hotspots_mermaid.exists())
            self.assertTrue(hotspots_dot.exists())

            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            review_targets_payload = json.loads(review_targets_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["contract_id"], "ProbeReport")
            self.assertEqual(payload["repo_root"], str(REPO_ROOT))
            self.assertEqual(payload["summary"]["probe_count"], 2)
            self.assertEqual(payload["summary"]["risk_hints"], 2)
            self.assertEqual(payload["summary"]["hints_by_severity"]["high"], 1)
            self.assertEqual(payload["summary"]["hints_by_probe"]["probe_clone_density"], 1)
            self.assertEqual(payload["summary"]["topology"]["edge_count"], 12)
            self.assertEqual(payload["summary"]["priority_hotspots"][0]["priority_score"], 148)
            self.assertEqual(len(payload["risk_hints"]), 2)
            self.assertEqual(payload["risk_hints"][0]["probe"], "probe_design_smells")
            self.assertTrue(payload["risk_hints"][0]["finding_id"])
            self.assertEqual(payload["risk_hints"][0]["rule_id"], "probe_design_smells")
            self.assertEqual(payload["findings"][0]["contract_id"], "Finding")
            self.assertEqual(payload["repo_policy"]["repo_name"], "VoiceTerm")
            self.assertIn("quality_scopes", payload["repo_policy"])
            self.assertIn(
                "python_probe_roots",
                payload["repo_policy"]["quality_scopes"],
            )
            self.assertIn("review_packet", payload)
            self.assertEqual(payload["review_packet"]["contract_id"], "ReviewPacket")
            self.assertEqual(payload["topology"]["contract_id"], "FileTopology")
            self.assertEqual(review_targets_payload["contract_id"], "ReviewTargets")
            self.assertEqual(review_targets_payload["findings"][0]["contract_id"], "Finding")

    def test_run_returns_error_when_probe_execution_fails(self) -> None:
        args = Namespace(
            since_ref=None,
            adoption_scan=False,
            head_ref="HEAD",
            quality_policy=None,
            output_root="dev/reports/probes",
            emit_artifacts=False,
            format="json",
            output=None,
            json_output=None,
            pipe_command=None,
            pipe_args=None,
        )

        with (
            patch(
                "dev.scripts.devctl.commands.probe_report.resolve_review_probe_script_ids",
                return_value=("probe_design_smells",),
            ),
            patch(
                "dev.scripts.devctl.review_probe_report.subprocess.run",
                return_value=CompletedProcess(["python3"], 2, stdout="", stderr="boom"),
            ),
            patch(
                "dev.scripts.devctl.review_probe_report.build_probe_topology_artifact",
                return_value=_topology_payload(),
            ),
            patch(
                "dev.scripts.devctl.review_probe_report.build_review_packet",
                return_value=_review_packet_payload(),
            ),
            patch(
                "dev.scripts.devctl.commands.probe_report.render_probe_report_markdown",
                return_value="# probe report",
            ),
            patch(
                "dev.scripts.devctl.review_probe_report.resolve_quality_policy",
                return_value=quality_policy.resolve_quality_policy(),
            ),
        ):
            rc = probe_report.run(args)

        self.assertEqual(rc, 1)

    def test_run_forwards_quality_policy_env_to_probe_subprocesses(self) -> None:
        args = Namespace(
            since_ref=None,
            adoption_scan=False,
            head_ref="HEAD",
            quality_policy="~/portable-policy.json",
            output_root="dev/reports/probes",
            emit_artifacts=False,
            format="json",
            output=None,
            json_output=None,
            pipe_command=None,
            pipe_args=None,
        )

        with (
            patch(
                "dev.scripts.devctl.commands.probe_report.resolve_review_probe_script_ids",
                return_value=("probe_design_smells",),
            ),
            patch(
                "dev.scripts.devctl.review_probe_report.subprocess.run",
                return_value=CompletedProcess(
                    ["python3"],
                    0,
                    stdout=json.dumps(_probe_payload("probe_design_smells")),
                    stderr="",
                ),
            ) as mock_run,
            patch(
                "dev.scripts.devctl.review_probe_report.build_probe_topology_artifact",
                return_value=_topology_payload(),
            ),
            patch(
                "dev.scripts.devctl.review_probe_report.build_review_packet",
                return_value=_review_packet_payload(),
            ),
            patch(
                "dev.scripts.devctl.commands.probe_report.render_probe_report_markdown",
                return_value="# probe report",
            ),
            patch(
                "dev.scripts.devctl.review_probe_report.resolve_quality_policy",
                return_value=quality_policy.resolve_quality_policy(),
            ),
        ):
            rc = probe_report.run(args)

        self.assertEqual(rc, 0)
        env = mock_run.call_args.kwargs["env"]
        self.assertEqual(
            env[QUALITY_POLICY_ENV_VAR],
            str(Path("~/portable-policy.json").expanduser()),
        )

    def test_run_supports_adoption_scan_forwarding(self) -> None:
        args = Namespace(
            since_ref=None,
            adoption_scan=True,
            head_ref="HEAD",
            quality_policy=None,
            output_root="dev/reports/probes",
            emit_artifacts=False,
            format="json",
            output=None,
            json_output=None,
            pipe_command=None,
            pipe_args=None,
        )

        with (
            patch(
                "dev.scripts.devctl.commands.probe_report.resolve_review_probe_script_ids",
                return_value=("probe_design_smells",),
            ),
            patch(
                "dev.scripts.devctl.review_probe_report.subprocess.run",
                return_value=CompletedProcess(
                    ["python3"],
                    0,
                    stdout=json.dumps(_probe_payload("probe_design_smells")),
                    stderr="",
                ),
            ) as mock_run,
            patch(
                "dev.scripts.devctl.review_probe_report.build_probe_topology_artifact",
                return_value=_topology_payload(),
            ),
            patch(
                "dev.scripts.devctl.review_probe_report.build_review_packet",
                return_value=_review_packet_payload(),
            ),
            patch(
                "dev.scripts.devctl.commands.probe_report.render_probe_report_markdown",
                return_value="# probe report",
            ),
            patch(
                "dev.scripts.devctl.review_probe_report.resolve_quality_policy",
                return_value=quality_policy.resolve_quality_policy(),
            ),
        ):
            rc = probe_report.run(args)

        self.assertEqual(rc, 0)
        cmd = mock_run.call_args.args[0]
        self.assertIn(ADOPTION_BASE_REF, cmd)
        self.assertIn(WORKTREE_HEAD_REF, cmd)

    def test_run_uses_external_repo_policy_and_restores_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "dev" / "config").mkdir(parents=True)
            (repo_root / "dev" / "config" / "devctl_repo_policy.json").write_text(
                json.dumps({"repo_name": "external-demo"}),
                encoding="utf-8",
            )
            output_root = repo_root / "probe-output"
            args = Namespace(
                since_ref=None,
                adoption_scan=False,
                head_ref="HEAD",
                quality_policy=None,
                output_root=str(output_root),
                emit_artifacts=True,
                format="json",
                output=str(repo_root / "probe-report.json"),
                json_output=None,
                pipe_command=None,
                pipe_args=None,
                repo_path=str(repo_root),
            )

            with (
                patch(
                    "dev.scripts.devctl.review_probe_report.subprocess.run",
                    return_value=CompletedProcess(
                        ["python3"],
                        0,
                        stdout=json.dumps(_probe_payload("probe_design_smells")),
                        stderr="",
                    ),
                ),
                patch(
                    "dev.scripts.devctl.review_probe_report.build_probe_topology_artifact",
                    return_value=_topology_payload(),
                ),
                patch(
                    "dev.scripts.devctl.review_probe_report.build_review_packet",
                    return_value=_review_packet_payload(),
                ),
                patch(
                    "dev.scripts.devctl.commands.probe_report.render_probe_report_markdown",
                    return_value="# probe report",
                ),
            ):
                rc = probe_report.run(args)

            payload = json.loads((repo_root / "probe-report.json").read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(payload["repo_policy"]["repo_name"], "external-demo")
        self.assertEqual(payload["repo_root"], str(repo_root.resolve()))
        self.assertEqual(
            Path(payload["artifact_paths"]["summary_json"]).resolve().parent.parent,
            output_root.resolve(),
        )
        self.assertEqual(get_repo_root(), REPO_ROOT)


class ProbeReportParserTests(unittest.TestCase):
    def test_cli_parser_accepts_probe_report_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "probe-report",
                "--since-ref",
                "origin/develop",
                "--head-ref",
                "HEAD",
                "--quality-policy",
                "/tmp/portable-policy.json",
                "--format",
                "terminal",
                "--output-root",
                "/tmp/probes",
            ]
        )

        self.assertEqual(args.command, "probe-report")
        self.assertEqual(args.since_ref, "origin/develop")
        self.assertEqual(args.head_ref, "HEAD")
        self.assertEqual(args.quality_policy, "/tmp/portable-policy.json")
        self.assertEqual(args.format, "terminal")
        self.assertEqual(args.output_root, "/tmp/probes")

    def test_cli_parser_accepts_adoption_scan_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["probe-report", "--adoption-scan"])

        self.assertEqual(args.command, "probe-report")
        self.assertTrue(args.adoption_scan)


if __name__ == "__main__":
    unittest.main()
