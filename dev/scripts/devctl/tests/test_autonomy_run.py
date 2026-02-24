"""Tests for devctl autonomy-run parser and command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import autonomy_run


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "repo": "owner/repo",
        "run_label": "autonomy-run-test",
        "plan_doc": "dev/active/autonomous_control_plane.md",
        "index_doc": "dev/active/INDEX.md",
        "master_plan_doc": "dev/active/MASTER_PLAN.md",
        "mp_scope": "MP-338",
        "next_steps_limit": 8,
        "question": None,
        "run_root": "dev/reports/autonomy/runs",
        "swarm_output_root": "dev/reports/autonomy/swarms",
        "branch_base": "develop",
        "mode": "report-only",
        "fix_command": None,
        "agents": None,
        "adaptive": True,
        "min_agents": 4,
        "max_agents": 20,
        "token_budget": 0,
        "per_agent_token_cost": 12000,
        "parallel_workers": 2,
        "agent_timeout_seconds": 120,
        "max_rounds": 1,
        "max_hours": 1.0,
        "max_tasks": 1,
        "checkpoint_every": 1,
        "loop_max_attempts": 1,
        "dry_run": True,
        "diff_ref": "origin/develop",
        "target_paths": [],
        "charts": False,
        "audit_source_root": "dev/reports/autonomy",
        "audit_library_root": "dev/reports/autonomy/library",
        "audit_event_log": "dev/reports/audits/devctl_events.jsonl",
        "stale_minutes": 120,
        "skip_governance": False,
        "skip_plan_update": False,
        "continuous": False,
        "continuous_max_cycles": 10,
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
                "- [ ] Scope lane assignments for next swarm run",
                "- [ ] Confirm reviewer lane stays healthy before merge",
                "",
                "## Progress Log",
                "",
                "- 2026-02-24: Existing progress item.",
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


class AutonomyRunParserTests(unittest.TestCase):
    def test_cli_accepts_autonomy_run_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "autonomy-run",
                "--plan-doc",
                "dev/active/autonomous_control_plane.md",
                "--mp-scope",
                "MP-338",
                "--next-steps-limit",
                "6",
                "--agents",
                "10",
                "--mode",
                "report-only",
                "--fix-command",
                "echo run-fix",
                "--no-charts",
                "--continuous",
                "--continuous-max-cycles",
                "7",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "autonomy-run")
        self.assertEqual(args.next_steps_limit, 6)
        self.assertEqual(args.agents, 10)
        self.assertEqual(args.fix_command, "echo run-fix")
        self.assertFalse(args.charts)
        self.assertTrue(args.continuous)
        self.assertEqual(args.continuous_max_cycles, 7)
        self.assertEqual(args.format, "json")


class AutonomyRunCommandTests(unittest.TestCase):
    def test_run_executes_pipeline_and_updates_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            plan_doc = root / "autonomous_control_plane.md"
            index_doc = root / "INDEX.md"
            master_doc = root / "MASTER_PLAN.md"
            output_json = root / "autonomy-run.json"
            run_root = root / "runs"
            swarm_root = root / "swarms"

            _write_plan_fixture(plan_doc)
            index_doc.write_text(
                "| Path | Role | Execution authority | MP scope | When agents read |\n"
                "|---|---|---|---|---|\n"
                "| `autonomous_control_plane.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-325..MP-338` | always |\n",
                encoding="utf-8",
            )
            master_doc.write_text(
                "- [ ] MP-338 loop-output-to-chat coordination lane\n", encoding="utf-8"
            )

            args = make_args(
                run_label="pipeline-001",
                plan_doc=str(plan_doc),
                index_doc=str(index_doc),
                master_plan_doc=str(master_doc),
                run_root=str(run_root),
                swarm_output_root=str(swarm_root),
                fix_command="echo run-fix",
                output=str(output_json),
            )

            def fake_run(command, timeout_seconds=0):
                command_text = " ".join(command)
                if "autonomy-swarm" in command:
                    self.assertIn("--fix-command", command)
                    self.assertIn("echo run-fix", command)
                    md_path = Path(command[command.index("--output") + 1])
                    json_path = Path(command[command.index("--json-output") + 1])
                    md_path.parent.mkdir(parents=True, exist_ok=True)
                    payload = {
                        "ok": True,
                        "summary": {
                            "selected_agents": 4,
                            "worker_agents": 3,
                            "reviewer_lane": True,
                        },
                        "post_audit": {"enabled": True, "ok": True},
                    }
                    md_path.write_text("# swarm\n", encoding="utf-8")
                    json_path.write_text(json.dumps(payload), encoding="utf-8")
                    return {
                        "command": command,
                        "returncode": 0,
                        "ok": True,
                        "stdout": "swarm ok",
                        "stderr": "",
                    }
                return {
                    "command": command,
                    "returncode": 0,
                    "ok": True,
                    "stdout": "ok",
                    "stderr": "",
                }

            with patch(
                "dev.scripts.devctl.commands.autonomy_run.resolve_repo",
                return_value="owner/repo",
            ), patch(
                "dev.scripts.devctl.commands.autonomy_run._run_command",
                side_effect=fake_run,
            ):
                rc = autonomy_run.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["swarm"]["ok"])
            self.assertTrue(payload["governance"]["ok"])
            self.assertTrue(payload["plan_update"]["ok"])
            self.assertTrue(payload["plan_update"]["updated"])
            self.assertEqual(
                payload["next_steps"][0], "Scope lane assignments for next swarm run"
            )
            self.assertTrue((Path(payload["run_dir"]) / "summary.md").exists())

            updated_plan = plan_doc.read_text(encoding="utf-8")
            self.assertIn("pipeline-001", updated_plan)
            self.assertIn("devctl autonomy-run", updated_plan)

    def test_run_returns_nonzero_when_governance_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            plan_doc = root / "autonomous_control_plane.md"
            index_doc = root / "INDEX.md"
            master_doc = root / "MASTER_PLAN.md"
            output_json = root / "autonomy-run.json"

            _write_plan_fixture(plan_doc)
            index_doc.write_text(
                "autonomous_control_plane.md MP-338\n", encoding="utf-8"
            )
            master_doc.write_text("MP-338\n", encoding="utf-8")

            args = make_args(
                run_label="pipeline-002",
                plan_doc=str(plan_doc),
                index_doc=str(index_doc),
                master_plan_doc=str(master_doc),
                run_root=str(root / "runs"),
                swarm_output_root=str(root / "swarms"),
                output=str(output_json),
            )

            def fake_run(command, timeout_seconds=0):
                command_text = " ".join(command)
                if "autonomy-swarm" in command:
                    md_path = Path(command[command.index("--output") + 1])
                    json_path = Path(command[command.index("--json-output") + 1])
                    md_path.parent.mkdir(parents=True, exist_ok=True)
                    md_path.write_text("# swarm\n", encoding="utf-8")
                    json_path.write_text(
                        json.dumps(
                            {
                                "ok": True,
                                "summary": {
                                    "selected_agents": 2,
                                    "worker_agents": 1,
                                    "reviewer_lane": True,
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return {
                        "command": command,
                        "returncode": 0,
                        "ok": True,
                        "stdout": "",
                        "stderr": "",
                    }
                if "check_multi_agent_sync.py" in command_text:
                    return {
                        "command": command,
                        "returncode": 1,
                        "ok": False,
                        "stdout": "",
                        "stderr": "sync failed",
                    }
                return {
                    "command": command,
                    "returncode": 0,
                    "ok": True,
                    "stdout": "",
                    "stderr": "",
                }

            with patch(
                "dev.scripts.devctl.commands.autonomy_run.resolve_repo",
                return_value="owner/repo",
            ), patch(
                "dev.scripts.devctl.commands.autonomy_run._run_command",
                side_effect=fake_run,
            ):
                rc = autonomy_run.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertFalse(payload["governance"]["ok"])
            failing_step = next(
                row
                for row in payload["governance"]["steps"]
                if row["name"] == "check_multi_agent_sync"
            )
            self.assertEqual(failing_step["returncode"], 1)
            self.assertFalse(failing_step["ok"])

    def test_continuous_mode_runs_multiple_cycles_until_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            plan_doc = root / "autonomous_control_plane.md"
            index_doc = root / "INDEX.md"
            master_doc = root / "MASTER_PLAN.md"
            output_json = root / "autonomy-run.json"

            _write_plan_fixture(plan_doc)
            index_doc.write_text("autonomous_control_plane.md MP-338\n", encoding="utf-8")
            master_doc.write_text("MP-338\n", encoding="utf-8")

            args = make_args(
                run_label="pipeline-cont",
                plan_doc=str(plan_doc),
                index_doc=str(index_doc),
                master_plan_doc=str(master_doc),
                run_root=str(root / "runs"),
                swarm_output_root=str(root / "swarms"),
                output=str(output_json),
                skip_governance=True,
                skip_plan_update=True,
                continuous=True,
                continuous_max_cycles=2,
            )

            def fake_run(command, timeout_seconds=0):
                command_text = " ".join(command)
                if "autonomy-swarm" in command_text:
                    md_path = Path(command[command.index("--output") + 1])
                    json_path = Path(command[command.index("--json-output") + 1])
                    md_path.parent.mkdir(parents=True, exist_ok=True)
                    md_path.write_text("# swarm\n", encoding="utf-8")
                    json_path.write_text(
                        json.dumps(
                            {
                                "ok": True,
                                "summary": {
                                    "selected_agents": 2,
                                    "worker_agents": 1,
                                    "reviewer_lane": True,
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return {
                        "command": command,
                        "returncode": 0,
                        "ok": True,
                        "stdout": "",
                        "stderr": "",
                    }
                return {
                    "command": command,
                    "returncode": 0,
                    "ok": True,
                    "stdout": "",
                    "stderr": "",
                }

            with patch(
                "dev.scripts.devctl.commands.autonomy_run.resolve_repo",
                return_value="owner/repo",
            ), patch(
                "dev.scripts.devctl.commands.autonomy_run._run_command",
                side_effect=fake_run,
            ):
                rc = autonomy_run.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["continuous"]["enabled"])
            self.assertEqual(payload["continuous"]["cycles_completed"], 2)
            self.assertEqual(payload["continuous"]["stop_reason"], "max_cycles_reached")
            self.assertEqual(len(payload["cycles"]), 2)


if __name__ == "__main__":
    unittest.main()
