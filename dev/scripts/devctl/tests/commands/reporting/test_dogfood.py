"""Tests for the dogfood reporting command."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.cli import COMMAND_HANDLERS, READ_ONLY_COMMANDS, build_parser
from dev.scripts.devctl.commands.listing import COMMANDS
from dev.scripts.devctl.commands.reporting import dogfood as command
from dev.scripts.devctl.config import REPO_ROOT, get_repo_root, set_repo_root


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

    def test_parser_accepts_campaign_metadata_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "dogfood",
                "--record",
                "--dev-mode",
                "--target-kind",
                "role",
                "--target-id",
                "reviewer",
                "--status",
                "passed",
                "--campaign-id",
                "campaign-voice-01",
                "--scenario-id",
                "scenario-dogfood-swarm",
                "--repo-scope",
                "voice-term",
                "--repo-label",
                "primary",
                "--repo-path",
                "/tmp/external-repo",
                "--topology",
                "multi_agent_orchestrated",
                "--lane-role",
                "reviewer",
                "--live-run-ref",
                "run-001",
                "run-002",
                "--governance-finding-id",
                "finding-abc",
                "finding-def",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.campaign_id, "campaign-voice-01")
        self.assertEqual(args.scenario_id, "scenario-dogfood-swarm")
        self.assertEqual(args.repo_scope, "voice-term")
        self.assertEqual(args.repo_label, "primary")
        self.assertEqual(args.repo_path, "/tmp/external-repo")
        self.assertEqual(args.topology, "multi_agent_orchestrated")
        self.assertEqual(args.lane_role, "reviewer")
        self.assertEqual(args.live_run_ref, ["run-001", "run-002"])
        self.assertEqual(args.governance_finding_id, ["finding-abc", "finding-def"])

    def test_handler_and_listing_registered(self) -> None:
        self.assertIn("dogfood", COMMAND_HANDLERS)
        self.assertIn("dogfood", COMMANDS)
        self.assertNotIn("dogfood", READ_ONLY_COMMANDS)
        self.assertIs(COMMAND_HANDLERS["dogfood"], command.run)

    def test_parser_accepts_governance_record_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "dogfood",
                "--record",
                "--record-governance",
                "--dev-mode",
                "--target-kind",
                "guard",
                "--target-id",
                "code_shape",
                "--status",
                "failed",
                "--governance-check-id",
                "dogfood.code_shape_push_regression",
                "--finding-path",
                "dev/scripts/devctl/commands/vcs/push.py",
                "--format",
                "json",
            ]
        )

        self.assertTrue(args.record_governance)
        self.assertEqual(
            args.governance_check_id,
            "dogfood.code_shape_push_regression",
        )
        self.assertEqual(
            args.finding_path,
            "dev/scripts/devctl/commands/vcs/push.py",
        )

    def test_parser_accepts_scenario_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "dogfood",
                "--run-scenario",
                "plan41-tandem",
                "--fix-mode",
                "isolated-worker",
                "--loop",
                "--max-cycles",
                "2",
                "--cadence-seconds",
                "330",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.run_scenario, "plan41-tandem")
        self.assertEqual(args.fix_mode, "isolated-worker")
        self.assertTrue(args.loop)
        self.assertEqual(args.max_cycles, 2)
        self.assertEqual(args.cadence_seconds, 330)


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
                    "--campaign-id",
                    "campaign-voice-01",
                    "--scenario-id",
                    "scenario-dogfood-swarm",
                    "--repo-scope",
                    "voice-term",
                    "--repo-label",
                    "primary",
                    "--repo-path",
                    str(root),
                    "--topology",
                    "multi_agent_orchestrated",
                    "--lane-role",
                    "reviewer",
                    "--live-run-ref",
                    "run-001",
                    "run-002",
                    "--governance-finding-id",
                    "finding-abc",
                    "finding-def",
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
            self.assertEqual(recorded_rows[0]["campaign_id"], "campaign-voice-01")
            self.assertEqual(recorded_rows[0]["scenario_id"], "scenario-dogfood-swarm")
            self.assertEqual(recorded_rows[0]["repo_scope"], "voice-term")
            self.assertEqual(recorded_rows[0]["repo_label"], "primary")
            self.assertEqual(recorded_rows[0]["repo_path"], str(root))
            self.assertEqual(recorded_rows[0]["topology"], "multi_agent_orchestrated")
            self.assertEqual(recorded_rows[0]["lane_role"], "reviewer")
            self.assertEqual(recorded_rows[0]["live_run_refs"], ["run-001", "run-002"])
            self.assertEqual(
                recorded_rows[0]["governance_finding_ids"],
                ["finding-abc", "finding-def"],
            )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["command"], "dogfood")
            self.assertEqual(payload["recorded"]["target_id"], "dogfood")
            self.assertEqual(payload["recorded"]["campaign_id"], "campaign-voice-01")
            self.assertEqual(
                payload["recorded"]["live_run_refs"],
                ["run-001", "run-002"],
            )

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
            self.assertEqual(
                summary_payload["recent_records"][0]["campaign_id"],
                "campaign-voice-01",
            )
            self.assertEqual(
                summary_payload["recent_records"][0]["live_run_refs"],
                ["run-001", "run-002"],
            )
            self.assertIn(
                "campaign_id=campaign-voice-01",
                summary_md.read_text(encoding="utf-8"),
            )

    def test_record_governance_defaults_from_target_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            log_path = root / "dogfood.jsonl"
            summary_root = root / "summary"
            output_path = root / "dogfood-output.json"
            governance_log = root / "finding_reviews.jsonl"
            governance_summary_root = root / "governance-summary"
            promotion_queue = root / "promotion.jsonl"
            parser = build_parser()
            args = parser.parse_args(
                [
                    "dogfood",
                    "--record",
                    "--record-governance",
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
                    "failed",
                    "--campaign-id",
                    "campaign-voice-01",
                    "--scenario-id",
                    "scenario-dogfood-swarm",
                    "--repo-scope",
                    "voice-term",
                    "--repo-label",
                    "primary",
                    "--live-run-ref",
                    "run-001",
                    "--governance-finding-id",
                    "finding-abc",
                    "--output",
                    str(output_path),
                    "--format",
                    "json",
                ]
            )

            with (
                patch.object(
                    command.dogfood_governance_support,
                    "resolve_governance_review_log_path",
                    return_value=governance_log,
                ),
                patch.object(
                    command.dogfood_governance_support,
                    "resolve_governance_review_summary_root",
                    return_value=governance_summary_root,
                ),
                patch.object(
                    command.dogfood_governance_support,
                    "resolve_guard_promotion_queue_path",
                    return_value=promotion_queue,
                ),
            ):
                self.assertEqual(command.run(args), 0)

            governance_rows = [
                json.loads(line)
                for line in governance_log.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(governance_rows), 1)
            self.assertEqual(governance_rows[0]["signal_type"], "dogfood")
            self.assertEqual(governance_rows[0]["verdict"], "confirmed_issue")
            self.assertEqual(
                governance_rows[0]["check_id"],
                "dogfood.command.dogfood",
            )
            self.assertEqual(
                governance_rows[0]["file_path"],
                "dev/scripts/devctl/commands/reporting/dogfood.py",
            )
            self.assertIn("campaign_id=campaign-voice-01", governance_rows[0]["notes"])
            self.assertIn("live_run_refs=[run-001]", governance_rows[0]["notes"])

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["governance_review"]["recorded"]["check_id"],
                "dogfood.command.dogfood",
            )
            self.assertFalse(payload["governance_review"]["promotion_candidate_created"])
            self.assertTrue((governance_summary_root / "review_summary.json").is_file())

    def test_record_governance_keeps_stable_finding_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            log_path = root / "dogfood.jsonl"
            summary_root = root / "summary"
            governance_log = root / "finding_reviews.jsonl"
            governance_summary_root = root / "governance-summary"
            promotion_queue = root / "promotion.jsonl"
            parser = build_parser()

            for status in ("failed", "passed"):
                args = parser.parse_args(
                    [
                        "dogfood",
                        "--record",
                        "--record-governance",
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
                        status,
                        "--format",
                        "json",
                    ]
                )
                with (
                    patch.object(
                        command.dogfood_governance_support,
                        "resolve_governance_review_log_path",
                        return_value=governance_log,
                    ),
                    patch.object(
                        command.dogfood_governance_support,
                        "resolve_governance_review_summary_root",
                        return_value=governance_summary_root,
                    ),
                    patch.object(
                        command.dogfood_governance_support,
                        "resolve_guard_promotion_queue_path",
                        return_value=promotion_queue,
                    ),
                ):
                    self.assertEqual(command.run(args), 0)

            governance_rows = [
                json.loads(line)
                for line in governance_log.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(governance_rows), 2)
            self.assertEqual(
                governance_rows[0]["finding_id"],
                governance_rows[1]["finding_id"],
            )
            self.assertEqual(governance_rows[0]["verdict"], "confirmed_issue")
            self.assertEqual(governance_rows[1]["verdict"], "fixed")

    def test_record_governance_requires_resolvable_or_explicit_finding_path(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "dogfood",
                "--record",
                "--record-governance",
                "--dev-mode",
                "--target-kind",
                "command",
                "--target-id",
                "not-a-real-command",
                "--status",
                "failed",
                "--format",
                "json",
            ]
        )

        self.assertEqual(command.run(args), 2)

    def test_record_governance_honors_override_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            log_path = root / "dogfood.jsonl"
            summary_root = root / "summary"
            governance_log = root / "finding_reviews.jsonl"
            governance_summary_root = root / "governance-summary"
            promotion_queue = root / "promotion.jsonl"
            parser = build_parser()
            args = parser.parse_args(
                [
                    "dogfood",
                    "--record",
                    "--record-governance",
                    "--dev-mode",
                    "--log-path",
                    str(log_path),
                    "--summary-root",
                    str(summary_root),
                    "--target-kind",
                    "guard",
                    "--target-id",
                    "code_shape",
                    "--status",
                    "failed",
                    "--governance-check-id",
                    "dogfood.code_shape_push_regression",
                    "--finding-path",
                    "dev/scripts/devctl/commands/vcs/push.py",
                    "--finding-class",
                    "local_defect",
                    "--recurrence-risk",
                    "recurring",
                    "--prevention-surface",
                    "guard",
                    "--notes",
                    "Push preflight bridge sync expanded push.py beyond the hard limit.",
                    "--format",
                    "json",
                ]
            )
            with (
                patch.object(
                    command.dogfood_governance_support,
                    "resolve_governance_review_log_path",
                    return_value=governance_log,
                ),
                patch.object(
                    command.dogfood_governance_support,
                    "resolve_governance_review_summary_root",
                    return_value=governance_summary_root,
                ),
                patch.object(
                    command.dogfood_governance_support,
                    "resolve_guard_promotion_queue_path",
                    return_value=promotion_queue,
                ),
            ):
                self.assertEqual(command.run(args), 0)

            governance_row = json.loads(
                governance_log.read_text(encoding="utf-8").splitlines()[0]
            )
            self.assertEqual(
                governance_row["check_id"],
                "dogfood.code_shape_push_regression",
            )
            self.assertEqual(
                governance_row["file_path"],
                "dev/scripts/devctl/commands/vcs/push.py",
            )
            self.assertEqual(governance_row["finding_class"], "local_defect")
            self.assertEqual(governance_row["prevention_surface"], "guard")

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

    def test_run_scenario_reports_router_and_tester_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output_path = root / "scenario.json"
            parser = build_parser()
            args = parser.parse_args(
                [
                    "dogfood",
                    "--run-scenario",
                    "plan41-tandem",
                    "--log-path",
                    str(root / "dogfood.jsonl"),
                    "--summary-root",
                    str(root / "summary"),
                    "--output",
                    str(output_path),
                    "--format",
                    "json",
                ]
            )

            with patch.object(
                command,
                "build_dashboard_snapshot",
                return_value=_scenario_dashboard(),
            ):
                self.assertEqual(command.run(args), 0)

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            scenario = payload["scenario"]
            self.assertEqual(scenario["scenario_id"], "plan41-tandem")
            self.assertEqual(scenario["scenario_state"], "ready_observe_only")
            self.assertEqual(scenario["dogfood_status"], "passed")
            self.assertEqual(scenario["router"]["router_state"], "ready")
            self.assertEqual(scenario["router"]["route_count"], 1)
            self.assertIn(
                "claude-tester",
                {lane["lane_id"] for lane in scenario["lanes"]},
            )
            self.assertIn(
                "packet_queue",
                {gate["gate_id"] for gate in scenario["gates"]},
            )

    def test_run_scenario_record_defaults_to_scenario_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            log_path = root / "dogfood.jsonl"
            output_path = root / "scenario.json"
            parser = build_parser()
            args = parser.parse_args(
                [
                    "dogfood",
                    "--record",
                    "--dev-mode",
                    "--run-scenario",
                    "plan41-tandem",
                    "--log-path",
                    str(log_path),
                    "--summary-root",
                    str(root / "summary"),
                    "--output",
                    str(output_path),
                    "--format",
                    "json",
                ]
            )

            with patch.object(
                command,
                "build_dashboard_snapshot",
                return_value=_scenario_dashboard(checkpoint_blocked=True),
            ):
                self.assertEqual(command.run(args), 0)

            row = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(row["target_kind"], "scenario")
            self.assertEqual(row["target_id"], "plan41-tandem")
            self.assertEqual(row["status"], "blocked")
            self.assertEqual(row["scenario_id"], "plan41-tandem")
            self.assertIn("blocked_by_startup_authority", row["notes"])

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["recorded"]["target_kind"], "scenario")
            self.assertEqual(
                payload["scenario"]["scenario_state"],
                "blocked_by_startup_authority",
            )

    def test_run_scenario_blocks_worker_modes_without_fanout_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output_path = root / "scenario.json"
            parser = build_parser()
            args = parser.parse_args(
                [
                    "dogfood",
                    "--run-scenario",
                    "plan41-tandem",
                    "--fix-mode",
                    "isolated-worker",
                    "--log-path",
                    str(root / "dogfood.jsonl"),
                    "--summary-root",
                    str(root / "summary"),
                    "--output",
                    str(output_path),
                    "--format",
                    "json",
                ]
            )

            with patch.object(
                command,
                "build_dashboard_snapshot",
                return_value=_scenario_dashboard(),
            ):
                self.assertEqual(command.run(args), 0)

            scenario = json.loads(output_path.read_text(encoding="utf-8"))["scenario"]
            self.assertEqual(scenario["scenario_state"], "blocked_by_fanout")
            fanout_gate = next(
                gate for gate in scenario["gates"] if gate["gate_id"] == "fanout_readiness"
            )
            self.assertTrue(fanout_gate["blocking"])
            self.assertEqual(fanout_gate["status"], "blocked")


class DogfoodPathResolutionTests(unittest.TestCase):
    def test_resolve_dogfood_log_path_uses_runtime_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            previous_root = get_repo_root()
            try:
                set_repo_root(repo_root)
                resolved = command.resolve_dogfood_log_path()
            finally:
                set_repo_root(previous_root)

        self.assertEqual(
            resolved,
            (repo_root / "dev" / "reports" / "dogfood" / "runs.jsonl").resolve(),
        )
        self.assertEqual(get_repo_root(), REPO_ROOT)


def _scenario_dashboard(*, checkpoint_blocked: bool = False) -> dict[str, object]:
    next_action = (
        "checkpoint_blocked_by_startup_authority:staged_index_budget_exceeded"
        if checkpoint_blocked
        else "run_next_tandem_packet"
    )
    top_blocker = "startup authority: staged_index_budget_exceeded" if checkpoint_blocked else ""
    attention = "checkpoint_required" if checkpoint_blocked else "healthy"
    return {
        "control_plane": {
            "next_action": next_action,
            "top_blocker": top_blocker,
            "attention_status": attention,
            "coordination": {
                "safe_to_fanout": False,
                "resync_required": False,
            },
            "session_posture": {
                "actors": [
                    {
                        "actor_id": "codex",
                        "provider": "codex",
                        "role": "reviewer",
                        "granted_capabilities": ["repo.commit"],
                    }
                ]
            },
        },
        "_review_state": {
            "queue": {"pending_total": 1},
            "agent_dispatch_router": {
                "contract_id": "AgentDispatchRouter",
                "schema_version": 1,
                "router_state": "ready",
                "selected_route_id": "route:codex|reviewer|s1|rev_pkt_1",
                "selected_route_ids": ["route:codex|reviewer|s1|rev_pkt_1"],
                "selection_reason": "single scoped route",
                "routes": [{"route_id": "route:codex|reviewer|s1|rev_pkt_1"}],
                "rejected_routes": [],
                "ambiguous_session_groups": [],
                "governance_debt": [],
            },
        },
        "agent_minds": {
            "codex": {
                "available": True,
                "generated_at_utc": "2026-05-01T21:21:00Z",
            },
            "claude": {
                "available": True,
                "generated_at_utc": "2026-05-01T21:21:00Z",
            },
        },
    }
