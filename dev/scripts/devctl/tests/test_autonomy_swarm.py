"""Tests for devctl autonomy-swarm parser and command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl import autonomy_swarm_helpers
from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import autonomy_swarm


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "repo": "owner/repo",
        "run_label": "swarm-test",
        "output_root": "dev/reports/autonomy/swarms",
        "agents": None,
        "adaptive": True,
        "min_agents": 1,
        "max_agents": 20,
        "question": "large refactor with parser + security hardening",
        "question_file": None,
        "prompt_tokens": 24000,
        "diff_ref": "origin/develop",
        "target_paths": [],
        "token_budget": 0,
        "per_agent_token_cost": 12000,
        "branch_base": "develop",
        "mode": "report-only",
        "fix_command": None,
        "max_rounds": 1,
        "max_hours": 1.0,
        "max_tasks": 1,
        "checkpoint_every": 1,
        "loop_max_attempts": 1,
        "parallel_workers": 2,
        "agent_timeout_seconds": 1800,
        "plan_only": False,
        "dry_run": True,
        "reviewer_lane": False,
        "post_audit": False,
        "audit_run_label": None,
        "audit_source_root": "dev/reports/autonomy",
        "audit_library_root": "dev/reports/autonomy/library",
        "audit_event_log": "dev/reports/audits/devctl_events.jsonl",
        "audit_refresh_orchestrate": False,
        "audit_copy_sources": True,
        "audit_charts": False,
        "charts": False,
        "format": "json",
        "output": None,
        "json_output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class AutonomySwarmParserTests(unittest.TestCase):
    def test_cli_accepts_autonomy_swarm_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "autonomy-swarm",
                "--question",
                "complex refactor",
                "--prompt-tokens",
                "32000",
                "--min-agents",
                "2",
                "--max-agents",
                "12",
                "--token-budget",
                "60000",
                "--parallel-workers",
                "3",
                "--fix-command",
                "echo swarm-fix",
                "--plan-only",
                "--no-post-audit",
                "--no-reviewer-lane",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "autonomy-swarm")
        self.assertEqual(args.prompt_tokens, 32000)
        self.assertEqual(args.min_agents, 2)
        self.assertEqual(args.max_agents, 12)
        self.assertEqual(args.token_budget, 60000)
        self.assertEqual(args.parallel_workers, 3)
        self.assertEqual(args.fix_command, "echo swarm-fix")
        self.assertTrue(args.plan_only)
        self.assertFalse(args.post_audit)
        self.assertFalse(args.reviewer_lane)


class AutonomySwarmCommandTests(unittest.TestCase):
    def test_fix_mode_requires_fix_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            args = make_args(
                output_root=str(Path(tmp_dir) / "swarms"),
                mode="fix-only",
                fix_command=None,
                output=str(Path(tmp_dir) / "swarm.json"),
            )
            rc = autonomy_swarm.run(args)

            self.assertEqual(rc, 2)

    @patch("dev.scripts.devctl.commands.autonomy_swarm.recommend_agent_count")
    @patch("dev.scripts.devctl.commands.autonomy_swarm.collect_refactor_metadata")
    def test_plan_only_emits_allocation_report(
        self,
        metadata_mock,
        recommend_mock,
    ) -> None:
        metadata_mock.return_value = (
            {
                "files_changed": 22,
                "lines_changed": 4200,
                "prompt_tokens": 18000,
                "difficulty_hits": ["refactor", "parser"],
            },
            [],
        )
        recommend_mock.return_value = (
            6,
            ["heuristic selected 6 agents"],
            {
                "base": 1.0,
                "lines_factor": 3.5,
                "files_factor": 2.2,
                "difficulty_factor": 1.4,
                "prompt_factor": 2.5,
                "raw_score": 10.6,
                "token_cap": None,
            },
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "swarm.json"
            args = make_args(
                output_root=str(Path(tmp_dir) / "swarms"),
                plan_only=True,
                output=str(output_path),
            )

            rc = autonomy_swarm.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["summary"]["selected_agents"], 6)
            self.assertEqual(payload["summary"]["executed_agents"], 0)

    @patch("dev.scripts.devctl.commands.autonomy_swarm._run_one_agent")
    @patch("dev.scripts.devctl.commands.autonomy_swarm.recommend_agent_count")
    @patch("dev.scripts.devctl.commands.autonomy_swarm.collect_refactor_metadata")
    def test_execute_swarm_aggregates_agent_results(
        self,
        metadata_mock,
        recommend_mock,
        run_one_agent_mock,
    ) -> None:
        metadata_mock.return_value = (
            {
                "files_changed": 3,
                "lines_changed": 120,
                "prompt_tokens": 2000,
                "difficulty_hits": [],
            },
            [],
        )
        recommend_mock.return_value = (
            3,
            ["heuristic selected 3 agents"],
            {
                "base": 1.0,
                "lines_factor": 0.1,
                "files_factor": 0.3,
                "difficulty_factor": 0.0,
                "prompt_factor": 0.2,
                "raw_score": 1.6,
                "token_cap": None,
            },
        )

        def side_effect(task, _args, _run_label):
            return {
                "agent": task.name,
                "index": task.index,
                "returncode": 0,
                "ok": True,
                "resolved": True,
                "reason": "resolved",
                "rounds_completed": 1,
                "tasks_completed": 1,
                "report_json": str(task.output_dir / "autonomy-loop.json"),
                "report_md": str(task.output_dir / "autonomy-loop.md"),
                "stdout_log": str(task.output_dir / "stdout.log"),
                "stderr_log": str(task.output_dir / "stderr.log"),
            }

        run_one_agent_mock.side_effect = side_effect

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "swarm.json"
            args = make_args(
                output_root=str(Path(tmp_dir) / "swarms"),
                output=str(output_path),
                dry_run=True,
                charts=False,
            )

            rc = autonomy_swarm.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["executed_agents"], 3)
            self.assertEqual(payload["summary"]["ok_count"], 3)
            self.assertEqual(payload["summary"]["resolved_count"], 3)
            self.assertEqual(len(payload["agents"]), 3)

    @patch("dev.scripts.devctl.commands.autonomy_swarm._run_post_audit_digest")
    @patch("dev.scripts.devctl.commands.autonomy_swarm._run_one_agent")
    @patch("dev.scripts.devctl.commands.autonomy_swarm.recommend_agent_count")
    @patch("dev.scripts.devctl.commands.autonomy_swarm.collect_refactor_metadata")
    def test_execute_swarm_runs_post_audit_by_default(
        self,
        metadata_mock,
        recommend_mock,
        run_one_agent_mock,
        post_audit_mock,
    ) -> None:
        metadata_mock.return_value = (
            {
                "files_changed": 1,
                "lines_changed": 10,
                "prompt_tokens": 500,
                "difficulty_hits": [],
            },
            [],
        )
        recommend_mock.return_value = (
            1,
            ["heuristic selected 1 agent"],
            {
                "base": 1.0,
                "lines_factor": 0.01,
                "files_factor": 0.1,
                "difficulty_factor": 0.0,
                "prompt_factor": 0.1,
                "raw_score": 1.21,
                "token_cap": None,
            },
        )
        run_one_agent_mock.return_value = {
            "agent": "AGENT-1",
            "index": 1,
            "returncode": 0,
            "ok": True,
            "resolved": True,
            "reason": "resolved",
            "rounds_completed": 1,
            "tasks_completed": 1,
            "report_json": "a.json",
            "report_md": "a.md",
            "stdout_log": "out.log",
            "stderr_log": "err.log",
        }

        def annotate_post_audit(_args, run_label):
            return {
                "enabled": True,
                "ok": True,
                "run_label": f"{run_label}-digest",
                "bundle_dir": "/tmp/digest",
                "summary_json": "/tmp/digest/summary.json",
                "summary_md": "/tmp/digest/summary.md",
                "metrics": {},
                "warnings": [],
                "errors": [],
            }

        post_audit_mock.side_effect = annotate_post_audit

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "swarm.json"
            args = make_args(
                output_root=str(Path(tmp_dir) / "swarms"),
                output=str(output_path),
                post_audit=True,
                dry_run=True,
            )

            rc = autonomy_swarm.run(args)

            self.assertEqual(rc, 0)
            post_audit_mock.assert_called_once()
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["post_audit"]["enabled"])
            self.assertTrue(payload["post_audit"]["ok"])

    @patch("dev.scripts.devctl.commands.autonomy_swarm._run_post_audit_digest")
    @patch("dev.scripts.devctl.commands.autonomy_swarm._run_one_agent")
    @patch("dev.scripts.devctl.commands.autonomy_swarm.recommend_agent_count")
    @patch("dev.scripts.devctl.commands.autonomy_swarm.collect_refactor_metadata")
    def test_reviewer_lane_reserves_one_slot_and_appends_review_agent(
        self,
        metadata_mock,
        recommend_mock,
        run_one_agent_mock,
        post_audit_mock,
    ) -> None:
        metadata_mock.return_value = (
            {
                "files_changed": 5,
                "lines_changed": 200,
                "prompt_tokens": 2000,
                "difficulty_hits": [],
            },
            [],
        )
        recommend_mock.return_value = (
            3,
            ["heuristic selected 3 agents"],
            {
                "base": 1.0,
                "lines_factor": 0.2,
                "files_factor": 0.5,
                "difficulty_factor": 0.0,
                "prompt_factor": 0.28,
                "raw_score": 1.98,
                "token_cap": None,
            },
        )
        run_one_agent_mock.side_effect = [
            {
                "agent": "AGENT-1",
                "index": 1,
                "returncode": 0,
                "ok": True,
                "resolved": True,
                "reason": "resolved",
                "rounds_completed": 1,
                "tasks_completed": 1,
                "report_json": "a1.json",
                "report_md": "a1.md",
                "stdout_log": "a1.out",
                "stderr_log": "a1.err",
            },
            {
                "agent": "AGENT-2",
                "index": 2,
                "returncode": 0,
                "ok": True,
                "resolved": True,
                "reason": "resolved",
                "rounds_completed": 1,
                "tasks_completed": 1,
                "report_json": "a2.json",
                "report_md": "a2.md",
                "stdout_log": "a2.out",
                "stderr_log": "a2.err",
            },
        ]
        post_audit_mock.return_value = {
            "enabled": True,
            "ok": True,
            "run_label": "swarm-test-digest",
            "bundle_dir": "/tmp/digest",
            "summary_json": "/tmp/digest/summary.json",
            "summary_md": "/tmp/digest/summary.md",
            "metrics": {},
            "warnings": [],
            "errors": [],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "swarm.json"
            args = make_args(
                output_root=str(Path(tmp_dir) / "swarms"),
                output=str(output_path),
                post_audit=True,
                reviewer_lane=True,
                dry_run=True,
            )

            rc = autonomy_swarm.run(args)

            self.assertEqual(rc, 0)
            self.assertEqual(run_one_agent_mock.call_count, 2)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["selected_agents"], 3)
            self.assertEqual(payload["summary"]["worker_agents"], 2)
            self.assertTrue(payload["summary"]["reviewer_lane"])
            self.assertEqual(payload["summary"]["executed_agents"], 3)
            self.assertEqual(payload["agents"][-1]["agent"], "AGENT-REVIEW")

    @patch("dev.scripts.devctl.commands.autonomy_swarm_core.subprocess.run")
    def test_fallback_repo_from_origin_parses_dot_repo_names(self, run_mock) -> None:
        run_mock.return_value = SimpleNamespace(
            returncode=0,
            stdout="git@github.com:acme/voice.term.git\n",
            stderr="",
        )

        repo = autonomy_swarm._fallback_repo_from_origin()

        self.assertEqual(repo, "acme/voice.term")


class AutonomySwarmHelperTests(unittest.TestCase):
    @patch("dev.scripts.devctl.autonomy_swarm_helpers.subprocess.run")
    def test_diff_stats_falls_back_to_working_tree_when_range_empty(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            SimpleNamespace(returncode=0, stdout="", stderr=""),
            SimpleNamespace(
                returncode=0, stdout="12\t3\tdev/scripts/devctl/cli.py\n", stderr=""
            ),
        ]

        files, added, deleted, warnings = autonomy_swarm_helpers._diff_stats(
            "origin/develop", []
        )

        self.assertEqual((files, added, deleted), (1, 12, 3))
        self.assertEqual(warnings, [])
        self.assertEqual(run_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
