"""Tests for mutation_ralph_workflow_bridge workflow helper script."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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


class MutationRalphWorkflowBridgeTests(unittest.TestCase):
    """Protect workflow config validation/output behavior."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "mutation_ralph_workflow_bridge",
            "dev/scripts/mutation_ralph_workflow_bridge.py",
        )

    def test_resolve_dispatch_config_uses_dispatch_defaults(self) -> None:
        config = self.script.resolve_config_from_env(
            event_name="workflow_dispatch",
            env={
                "DISPATCH_BRANCH": "develop",
                "DISPATCH_MAX_ATTEMPTS": "",
                "DISPATCH_POLL_SECONDS": "",
                "DISPATCH_TIMEOUT_SECONDS": "",
                "DISPATCH_EXECUTION_MODE": "",
                "DISPATCH_THRESHOLD": "",
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
        self.assertEqual(config["execution_mode"], "report-only")
        self.assertEqual(config["threshold"], "0.80")
        self.assertEqual(config["notify_mode"], "summary-only")
        self.assertEqual(config["comment_target"], "auto")

    def test_resolve_workflow_config_uses_loop_values(self) -> None:
        config = self.script.resolve_config_from_env(
            event_name="workflow_run",
            env={
                "WORKFLOW_BRANCH": "feature/x",
                "LOOP_MAX_ATTEMPTS": "4",
                "LOOP_POLL_SECONDS": "30",
                "LOOP_TIMEOUT_SECONDS": "2400",
                "LOOP_EXECUTION_MODE": "plan-then-fix",
                "LOOP_THRESHOLD": "0.95",
                "LOOP_NOTIFY_MODE": "summary-and-comment",
                "LOOP_COMMENT_TARGET": "pr",
                "LOOP_COMMENT_PR_NUMBER": "123",
                "LOOP_FIX_COMMAND": "python3 fix.py",
            },
        )
        self.assertEqual(config["branch"], "feature/x")
        self.assertEqual(config["max_attempts"], "4")
        self.assertEqual(config["poll_seconds"], "30")
        self.assertEqual(config["timeout_seconds"], "2400")
        self.assertEqual(config["execution_mode"], "plan-then-fix")
        self.assertEqual(config["threshold"], "0.95")
        self.assertEqual(config["notify_mode"], "summary-and-comment")
        self.assertEqual(config["comment_target"], "pr")
        self.assertEqual(config["comment_pr_number"], "123")
        self.assertEqual(config["fix_command"], "python3 fix.py")

    def test_resolve_config_rejects_invalid_threshold(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid threshold: 1.4"):
            self.script.resolve_config_from_env(
                event_name="workflow_dispatch",
                env={"DISPATCH_BRANCH": "develop", "DISPATCH_THRESHOLD": "1.4"},
            )

    def test_write_config_outputs_preserves_multiline_fix_command(self) -> None:
        config = {
            "branch": "develop",
            "max_attempts": "3",
            "poll_seconds": "20",
            "timeout_seconds": "1800",
            "execution_mode": "report-only",
            "threshold": "0.80",
            "notify_mode": "summary-only",
            "comment_target": "auto",
            "comment_pr_number": "",
            "fix_command": "echo hi\necho bye",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "github_output.txt"
            self.script.write_config_outputs(config, output_path)
            self.assertEqual(
                output_path.read_text(encoding="utf-8").splitlines(),
                [
                    "branch=develop",
                    "max_attempts=3",
                    "poll_seconds=20",
                    "timeout_seconds=1800",
                    "execution_mode=report-only",
                    "threshold=0.80",
                    "notify_mode=summary-only",
                    "comment_target=auto",
                    "comment_pr_number=",
                    "fix_command<<EOF",
                    "echo hi",
                    "echo bye",
                    "EOF",
                ],
            )

    def test_extract_failure_reason_returns_trimmed_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "report.json"
            payload_path.write_text(
                json.dumps({"reason": " artifact download failed  "}),
                encoding="utf-8",
            )
            reason = self.script.extract_failure_reason(payload_path)
        self.assertEqual(reason, "artifact download failed")

    def test_build_loop_command_adds_optional_flags(self) -> None:
        args = self.script.argparse.Namespace(
            target_repo="owner/repo",
            target_branch="develop",
            max_attempts="3",
            poll_seconds="20",
            timeout_seconds="1800",
            mode="plan-then-fix",
            threshold="0.80",
            notify_mode="summary-only",
            comment_target="auto",
            comment_pr_number="123",
            fix_command="python3 fix.py",
            json_output="/tmp/mutation-ralph-loop.json",
            output="/tmp/mutation-ralph-loop.md",
        )
        command = self.script.build_loop_command(args)
        self.assertIn("--comment-pr-number", command)
        self.assertIn("123", command)
        self.assertIn("--fix-command", command)
        self.assertIn("python3 fix.py", command)

    def test_build_loop_command_skips_fix_command_for_report_only_mode(self) -> None:
        args = self.script.argparse.Namespace(
            target_repo="owner/repo",
            target_branch="develop",
            max_attempts="3",
            poll_seconds="20",
            timeout_seconds="1800",
            mode="report-only",
            threshold="0.80",
            notify_mode="summary-only",
            comment_target="auto",
            comment_pr_number="",
            fix_command="python3 fix.py",
            json_output="/tmp/mutation-ralph-loop.json",
            output="/tmp/mutation-ralph-loop.md",
        )
        command = self.script.build_loop_command(args)
        self.assertNotIn("--fix-command", command)

    def test_run_loop_soft_fails_artifact_download_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "loop.json"
            report_path.write_text(
                json.dumps({"reason": "artifact download failed"}),
                encoding="utf-8",
            )
            args = self.script.argparse.Namespace(
                target_repo="owner/repo",
                target_branch="develop",
                max_attempts="3",
                poll_seconds="20",
                timeout_seconds="1800",
                mode="report-only",
                threshold="0.80",
                notify_mode="summary-only",
                comment_target="auto",
                comment_pr_number="",
                fix_command="",
                json_output=str(report_path),
                output="/tmp/mutation-ralph-loop.md",
            )
            with mock.patch.object(
                self.script.subprocess,
                "run",
                return_value=self.script.subprocess.CompletedProcess(
                    args=[],
                    returncode=1,
                ),
            ):
                rc = self.script._run_loop_command(args)
        self.assertEqual(rc, 0)

    def test_run_loop_propagates_failure_when_reason_not_soft_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "loop.json"
            report_path.write_text(
                json.dumps({"reason": "other"}),
                encoding="utf-8",
            )
            args = self.script.argparse.Namespace(
                target_repo="owner/repo",
                target_branch="develop",
                max_attempts="3",
                poll_seconds="20",
                timeout_seconds="1800",
                mode="report-only",
                threshold="0.80",
                notify_mode="summary-only",
                comment_target="auto",
                comment_pr_number="",
                fix_command="",
                json_output=str(report_path),
                output="/tmp/mutation-ralph-loop.md",
            )
            with mock.patch.object(
                self.script.subprocess,
                "run",
                return_value=self.script.subprocess.CompletedProcess(
                    args=[],
                    returncode=1,
                ),
            ):
                rc = self.script._run_loop_command(args)
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
