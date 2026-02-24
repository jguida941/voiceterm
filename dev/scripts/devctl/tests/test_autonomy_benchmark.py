"""Tests for devctl autonomy-benchmark parser and command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.autonomy_benchmark_matrix import build_swarm_command
from dev.scripts.devctl.commands import autonomy_benchmark


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "repo": "owner/repo",
        "run_label": "benchmark-test",
        "plan_doc": "dev/active/autonomous_control_plane.md",
        "index_doc": "dev/active/INDEX.md",
        "master_plan_doc": "dev/active/MASTER_PLAN.md",
        "mp_scope": "MP-338",
        "next_steps_limit": 8,
        "question": "benchmark task",
        "question_file": None,
        "output_root": "dev/reports/autonomy/benchmarks",
        "swarm_counts": "10,15",
        "tactics": "uniform,test-first",
        "agents": 3,
        "parallel_workers": 2,
        "max_concurrent_swarms": 3,
        "branch_base": "develop",
        "mode": "report-only",
        "fix_command": None,
        "max_rounds": 1,
        "max_hours": 0.5,
        "max_tasks": 1,
        "loop_max_attempts": 1,
        "agent_timeout_seconds": 120,
        "diff_ref": "origin/develop",
        "target_paths": [],
        "token_budget": 0,
        "per_agent_token_cost": 12000,
        "post_audit": False,
        "reviewer_lane": False,
        "dry_run": True,
        "charts": False,
        "format": "json",
        "output": None,
        "json_output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _write_plan_fixture(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Autonomous Control Plane",
                "",
                "## Execution Checklist",
                "",
                "- [ ] Run swarm benchmark matrix",
                "- [ ] Compare tactic productivity",
                "",
                "## Progress Log",
                "",
                "- 2026-02-24: Existing item.",
                "",
                "## Audit Evidence",
                "",
                "| Check | Evidence | Status |",
                "|---|---|---|",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class AutonomyBenchmarkParserTests(unittest.TestCase):
    def test_cli_accepts_autonomy_benchmark_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "autonomy-benchmark",
                "--plan-doc",
                "dev/active/autonomous_control_plane.md",
                "--mp-scope",
                "MP-338",
                "--swarm-counts",
                "10,20,30",
                "--tactics",
                "uniform,test-first",
                "--agents",
                "4",
                "--fix-command",
                "echo benchmark-fix",
                "--max-concurrent-swarms",
                "12",
                "--no-charts",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "autonomy-benchmark")
        self.assertEqual(args.swarm_counts, "10,20,30")
        self.assertEqual(args.tactics, "uniform,test-first")
        self.assertEqual(args.agents, 4)
        self.assertEqual(args.fix_command, "echo benchmark-fix")
        self.assertEqual(args.max_concurrent_swarms, 12)
        self.assertFalse(args.charts)
        self.assertEqual(args.format, "json")


class AutonomyBenchmarkCommandTests(unittest.TestCase):
    def test_build_swarm_command_forwards_fix_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            args = make_args(
                fix_command="echo benchmark-fix",
                output_root=str(root / "benchmarks"),
            )
            command = build_swarm_command(
                args=args,
                repo="owner/repo",
                run_label="bench-001",
                question="q",
                output_md=root / "summary.md",
                output_json=root / "summary.json",
            )
            self.assertIn("--fix-command", command)
            self.assertIn("echo benchmark-fix", command)

    def test_command_emits_matrix_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            plan_doc = root / "autonomous_control_plane.md"
            index_doc = root / "INDEX.md"
            master_doc = root / "MASTER_PLAN.md"
            output_json = root / "benchmark.json"

            _write_plan_fixture(plan_doc)
            index_doc.write_text(
                "autonomous_control_plane.md MP-338\n", encoding="utf-8"
            )
            master_doc.write_text("MP-338\n", encoding="utf-8")

            args = make_args(
                plan_doc=str(plan_doc),
                index_doc=str(index_doc),
                master_plan_doc=str(master_doc),
                output_root=str(root / "benchmarks"),
                output=str(output_json),
            )

            def fake_scenario_payload(
                *,
                args,
                repo,
                benchmark_label,
                scenario,
                base_prompt,
                next_steps,
                benchmark_dir,
            ):
                self.assertTrue(repo)
                self.assertTrue(benchmark_label)
                self.assertTrue(base_prompt)
                self.assertTrue(next_steps)
                return {
                    "label": scenario.label,
                    "tactic": scenario.tactic,
                    "swarm_count": scenario.swarm_count,
                    "summary": {
                        "swarms_total": scenario.swarm_count,
                        "swarms_ok": scenario.swarm_count,
                        "swarms_failed": 0,
                        "tasks_completed_total": scenario.swarm_count,
                        "rounds_completed_total": scenario.swarm_count,
                        "work_output_score": scenario.swarm_count * 2,
                        "elapsed_seconds_total": float(scenario.swarm_count),
                        "tasks_per_minute": 10.0,
                        "swarm_success_pct": 100.0,
                    },
                    "swarms": [],
                    "scenario_dir": str(benchmark_dir / scenario.label),
                }

            with patch(
                "dev.scripts.devctl.commands.autonomy_benchmark.resolve_repo",
                return_value="owner/repo",
            ), patch(
                "dev.scripts.devctl.commands.autonomy_benchmark.run_scenario_payload",
                side_effect=fake_scenario_payload,
            ):
                rc = autonomy_benchmark.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["overall_summary"]["scenarios_total"], 4)
            self.assertEqual(payload["overall_summary"]["swarms_total"], 50)
            self.assertEqual(payload["overall_summary"]["swarms_failed"], 0)
            self.assertEqual(payload["overall_summary"]["tasks_completed_total"], 50)
            self.assertTrue(payload["leaders"]["best_work_output"]["label"])
            self.assertTrue((Path(payload["benchmark_dir"]) / "summary.md").exists())


if __name__ == "__main__":
    unittest.main()
