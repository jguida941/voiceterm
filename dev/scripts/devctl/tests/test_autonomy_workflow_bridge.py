"""Tests for autonomy workflow bridge helper script."""

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def load_module(name: str, relative_path: str):
    """Load a repository script as a module for unit tests."""
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AutonomyWorkflowBridgeTests(unittest.TestCase):
    """Protect workflow config resolution and export behavior."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "autonomy_workflow_bridge",
            "dev/scripts/workflow_bridge/autonomy.py",
        )

    def test_resolve_controller_dispatch_defaults_to_env_fallbacks(self) -> None:
        config = self.script.resolve_controller_config_from_env(
            event_name="workflow_dispatch",
            env={
                "INPUT_PLAN_ID": "MP-338",
                "INPUT_BRANCH_BASE": "",
                "INPUT_MODE": "",
                "INPUT_MAX_ROUNDS": "",
                "INPUT_MAX_HOURS": "",
                "INPUT_MAX_TASKS": "",
                "INPUT_CHECKPOINT_EVERY": "",
                "INPUT_LOOP_MAX_ATTEMPTS": "",
                "INPUT_NOTIFY_MODE": "",
                "INPUT_COMMENT_TARGET": "",
                "INPUT_COMMENT_PR_NUMBER": "77",
                "INPUT_ALLOW_AUTO_SEND": "true",
                "INPUT_FIX_COMMAND": "",
                "DEFAULT_MODE": "report-only",
                "DEFAULT_MAX_ROUNDS": "2",
                "DEFAULT_MAX_HOURS": "2",
                "DEFAULT_MAX_TASKS": "8",
                "DEFAULT_CHECKPOINT_EVERY": "1",
                "DEFAULT_LOOP_MAX_ATTEMPTS": "1",
                "DEFAULT_NOTIFY_MODE": "summary-only",
                "DEFAULT_COMMENT_TARGET": "auto",
            },
        )
        self.assertEqual(config["plan_id"], "MP-338")
        self.assertEqual(config["branch_base"], "develop")
        self.assertEqual(config["mode"], "report-only")
        self.assertEqual(config["max_rounds"], "2")
        self.assertEqual(config["max_hours"], "2")
        self.assertEqual(config["max_tasks"], "8")
        self.assertEqual(config["checkpoint_every"], "1")
        self.assertEqual(config["loop_max_attempts"], "1")
        self.assertEqual(config["notify_mode"], "summary-only")
        self.assertEqual(config["comment_target"], "auto")
        self.assertEqual(config["comment_pr_number"], "77")
        self.assertEqual(config["allow_auto_send"], "true")
        self.assertEqual(config["fix_command"], "")

    def test_resolve_controller_schedule_uses_scheduled_defaults(self) -> None:
        config = self.script.resolve_controller_config_from_env(
            event_name="schedule",
            env={
                "DEFAULT_MODE": "report-only",
                "DEFAULT_MAX_ROUNDS": "2",
                "DEFAULT_MAX_HOURS": "2",
                "DEFAULT_MAX_TASKS": "8",
                "DEFAULT_CHECKPOINT_EVERY": "1",
                "DEFAULT_LOOP_MAX_ATTEMPTS": "1",
                "DEFAULT_NOTIFY_MODE": "summary-only",
                "DEFAULT_COMMENT_TARGET": "auto",
            },
        )
        self.assertEqual(config["plan_id"], "scheduled-autonomy")
        self.assertEqual(config["branch_base"], "develop")
        self.assertEqual(config["allow_auto_send"], "false")
        self.assertEqual(config["fix_command"], "")

    def test_resolve_controller_rejects_invalid_max_rounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid max_rounds: nope"):
            self.script.resolve_controller_config_from_env(
                event_name="workflow_dispatch",
                env={
                    "INPUT_PLAN_ID": "MP-338",
                    "INPUT_BRANCH_BASE": "develop",
                    "INPUT_MAX_ROUNDS": "nope",
                    "INPUT_MAX_HOURS": "1",
                    "INPUT_MAX_TASKS": "1",
                    "INPUT_CHECKPOINT_EVERY": "1",
                    "INPUT_LOOP_MAX_ATTEMPTS": "1",
                },
            )

    def test_write_controller_outputs_preserves_multiline_fix_command(self) -> None:
        config = {
            "plan_id": "MP-338",
            "branch_base": "develop",
            "mode": "fix-only",
            "max_rounds": "2",
            "max_hours": "1.5",
            "max_tasks": "8",
            "checkpoint_every": "1",
            "loop_max_attempts": "1",
            "notify_mode": "summary-only",
            "comment_target": "auto",
            "comment_pr_number": "55",
            "allow_auto_send": "true",
            "fix_command": "echo hi\necho bye",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "github_output.txt"
            self.script.write_controller_config_outputs(config, output_path)
            self.assertEqual(
                output_path.read_text(encoding="utf-8").splitlines(),
                [
                    "plan_id=MP-338",
                    "branch_base=develop",
                    "mode=fix-only",
                    "max_rounds=2",
                    "max_hours=1.5",
                    "max_tasks=8",
                    "checkpoint_every=1",
                    "loop_max_attempts=1",
                    "notify_mode=summary-only",
                    "comment_target=auto",
                    "comment_pr_number=55",
                    "allow_auto_send=true",
                    "fix_command<<EOF",
                    "echo hi",
                    "echo bye",
                    "EOF",
                ],
            )

    def test_resolve_ralph_dispatch_defaults(self) -> None:
        config = self.script.resolve_ralph_config_from_env(
            event_name="workflow_dispatch",
            env={
                "DISPATCH_BRANCH": "develop",
                "DISPATCH_MAX_ATTEMPTS": "",
                "DISPATCH_POLL_SECONDS": "",
                "DISPATCH_TIMEOUT_SECONDS": "",
                "DISPATCH_EXECUTION_MODE": "",
                "DISPATCH_NOTIFY_MODE": "",
                "DISPATCH_COMMENT_TARGET": "",
                "DISPATCH_COMMENT_PR_NUMBER": "",
                "DISPATCH_FIX_COMMAND": "",
            },
        )
        self.assertEqual(config["branch"], "develop")
        self.assertEqual(config["max_attempts"], "3")
        self.assertEqual(config["poll_seconds"], "20")
        self.assertEqual(config["timeout_seconds"], "1800")
        self.assertEqual(config["execution_mode"], "plan-then-fix")
        self.assertEqual(config["notify_mode"], "summary-and-comment")
        self.assertEqual(config["comment_target"], "auto")
        self.assertEqual(config["source_event"], "workflow_dispatch")
        self.assertEqual(config["fix_command"], "")

    def test_resolve_ralph_workflow_run_defaults_fix_command(self) -> None:
        config = self.script.resolve_ralph_config_from_env(
            event_name="workflow_run",
            env={
                "WORKFLOW_BRANCH": "feature/x",
                "WORKFLOW_RUN_ID": "12345",
                "WORKFLOW_HEAD_SHA": "abc123",
                "LOOP_MAX_ATTEMPTS": "",
                "LOOP_POLL_SECONDS": "",
                "LOOP_TIMEOUT_SECONDS": "",
                "LOOP_EXECUTION_MODE": "",
                "LOOP_NOTIFY_MODE": "",
                "LOOP_COMMENT_TARGET": "",
                "LOOP_COMMENT_PR_NUMBER": "",
                "LOOP_FIX_COMMAND": "",
            },
        )
        self.assertEqual(config["source_event"], "workflow_run")
        self.assertEqual(config["source_run_id"], "12345")
        self.assertEqual(config["source_run_sha"], "abc123")
        self.assertEqual(
            config["fix_command"], "python3 dev/scripts/devctl.py check --profile ci"
        )

    def test_resolve_ralph_rejects_missing_workflow_run_id(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "workflow_run source requires numeric run id"
        ):
            self.script.resolve_ralph_config_from_env(
                event_name="workflow_run",
                env={
                    "WORKFLOW_BRANCH": "develop",
                    "WORKFLOW_RUN_ID": "",
                    "WORKFLOW_HEAD_SHA": "abc123",
                },
            )

    def test_write_ralph_outputs_preserves_multiline_fix_command(self) -> None:
        config = {
            "branch": "develop",
            "max_attempts": "3",
            "poll_seconds": "20",
            "timeout_seconds": "1800",
            "execution_mode": "plan-then-fix",
            "notify_mode": "summary-and-comment",
            "comment_target": "auto",
            "comment_pr_number": "77",
            "source_event": "workflow_dispatch",
            "source_run_id": "",
            "source_run_sha": "",
            "fix_command": "echo one\necho two",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "github_output.txt"
            self.script.write_ralph_config_outputs(config, output_path)
            self.assertEqual(
                output_path.read_text(encoding="utf-8").splitlines(),
                [
                    "branch=develop",
                    "max_attempts=3",
                    "poll_seconds=20",
                    "timeout_seconds=1800",
                    "execution_mode=plan-then-fix",
                    "notify_mode=summary-and-comment",
                    "comment_target=auto",
                    "comment_pr_number=77",
                    "source_event=workflow_dispatch",
                    "source_run_id=",
                    "source_run_sha=",
                    "fix_command<<EOF",
                    "echo one",
                    "echo two",
                    "EOF",
                ],
            )

    def test_resolve_swarm_defaults_and_label_generation(self) -> None:
        config = self.script.resolve_swarm_config_from_env(
            {
                "INPUT_RUN_LABEL": "",
                "INPUT_BRANCH_BASE": "",
                "INPUT_AGENTS": "",
                "INPUT_PARALLEL_WORKERS": "",
                "INPUT_MAX_ROUNDS": "",
                "INPUT_MAX_HOURS": "",
                "INPUT_MAX_TASKS": "",
                "INPUT_STALE_MINUTES": "",
                "GITHUB_RUN_ID": "100",
                "GITHUB_RUN_ATTEMPT": "2",
            }
        )
        self.assertEqual(config["run_label"], "gh-swarm-run-100-2")
        self.assertEqual(config["branch_base"], "develop")
        self.assertEqual(config["agents"], "10")
        self.assertEqual(config["parallel_workers"], "4")
        self.assertEqual(config["max_rounds"], "1")
        self.assertEqual(config["max_hours"], "1")
        self.assertEqual(config["max_tasks"], "1")
        self.assertEqual(config["stale_minutes"], "120")

    def test_resolve_swarm_rejects_invalid_numeric_input(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid numeric input: bad"):
            self.script.resolve_swarm_config_from_env(
                {
                    "INPUT_RUN_LABEL": "run-a",
                    "INPUT_AGENTS": "bad",
                    "INPUT_PARALLEL_WORKERS": "4",
                    "INPUT_MAX_ROUNDS": "1",
                    "INPUT_MAX_HOURS": "1",
                    "INPUT_MAX_TASKS": "1",
                    "INPUT_STALE_MINUTES": "120",
                }
            )

    def test_write_swarm_outputs_writes_expected_fields(self) -> None:
        config = {
            "run_label": "gh-swarm-run-1-1",
            "branch_base": "develop",
            "agents": "8",
            "parallel_workers": "3",
            "max_rounds": "2",
            "max_hours": "1.5",
            "max_tasks": "4",
            "stale_minutes": "60",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "github_output.txt"
            self.script.write_swarm_config_outputs(config, output_path)
            self.assertEqual(
                output_path.read_text(encoding="utf-8").splitlines(),
                [
                    "run_label=gh-swarm-run-1-1",
                    "branch_base=develop",
                    "agents=8",
                    "parallel_workers=3",
                    "max_rounds=2",
                    "max_hours=1.5",
                    "max_tasks=4",
                    "stale_minutes=60",
                ],
            )

    def test_export_controller_writes_expected_fields(self) -> None:
        payload = {
            "summary_json": "/tmp/summary.json",
            "latest_working_branch": "feature/test",
            "branch_base": "develop",
            "resolved": True,
            "controller_run_id": "run-123",
            "reason": "ok",
            "phone_status_latest_json": "/tmp/phone.json",
            "phone_status_latest_md": "/tmp/phone.md",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            input_file = tmp_root / "controller.json"
            output_file = tmp_root / "github_output.txt"
            input_file.write_text(json.dumps(payload), encoding="utf-8")

            args = argparse.Namespace(
                input_file=str(input_file),
                github_output=str(output_file),
            )
            rc = self.script.export_controller(args)

            self.assertEqual(rc, 0)
            lines = output_file.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines,
                [
                    "summary_json=/tmp/summary.json",
                    "latest_working_branch=feature/test",
                    "branch_base=develop",
                    "resolved=true",
                    "controller_run_id=run-123",
                    "reason=ok",
                    "phone_status_latest_json=/tmp/phone.json",
                    "phone_status_latest_md=/tmp/phone.md",
                ],
            )

    def test_export_swarm_writes_expected_fields(self) -> None:
        payload = {
            "ok": False,
            "run_dir": "/tmp/swarm",
            "swarm": {
                "summary": {
                    "selected_agents": 10,
                    "worker_agents": 8,
                    "reviewer_lane": "AGENT-REVIEW",
                }
            },
            "governance": {"ok": True},
            "plan_update": {"ok": True, "updated": False},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            input_file = tmp_root / "swarm.json"
            output_file = tmp_root / "github_output.txt"
            input_file.write_text(json.dumps(payload), encoding="utf-8")

            args = argparse.Namespace(
                input_file=str(input_file),
                github_output=str(output_file),
            )
            rc = self.script.export_swarm(args)

            self.assertEqual(rc, 0)
            lines = output_file.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines,
                [
                    "report_ok=false",
                    "run_dir=/tmp/swarm",
                    "swarm_selected_agents=10",
                    "swarm_worker_agents=8",
                    "reviewer_lane=AGENT-REVIEW",
                    "governance_ok=true",
                    "plan_update_ok=true",
                    "plan_update_updated=false",
                ],
            )

    def test_assert_swarm_ok_non_ok_payload_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "swarm.json"
            input_file.write_text('{"ok": false}', encoding="utf-8")
            args = argparse.Namespace(input_file=str(input_file))
            self.assertEqual(self.script.assert_swarm_ok(args), 1)

    def test_assert_swarm_ok_ok_payload_returns_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "swarm.json"
            input_file.write_text('{"ok": true}', encoding="utf-8")
            args = argparse.Namespace(input_file=str(input_file))
            self.assertEqual(self.script.assert_swarm_ok(args), 0)


if __name__ == "__main__":
    unittest.main()
