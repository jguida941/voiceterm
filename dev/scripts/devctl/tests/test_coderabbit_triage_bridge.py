"""Tests for CodeRabbit triage bridge helper script."""

import argparse
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
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


class CodeRabbitTriageBridgeTests(unittest.TestCase):
    """Protect workflow helper behavior for CodeRabbit triage steps."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "coderabbit_triage_bridge",
            "dev/scripts/coderabbit/bridge.py",
        )

    def test_enforce_command_fails_on_medium_plus(self) -> None:
        payload = {
            "items": [
                {"severity": "info", "category": "docs", "summary": "nit"},
                {"severity": "high", "category": "quality", "summary": "fix me"},
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            priority_file = Path(tmpdir) / "priority.json"
            priority_file.write_text(json.dumps(payload), encoding="utf-8")
            args = argparse.Namespace(priority_file=str(priority_file))
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = self.script.enforce_command(args)
            self.assertEqual(rc, 1)
            rendered = stdout.getvalue()
            self.assertIn("CodeRabbit gate failed", rendered)
            self.assertIn("[high] quality: fix me", rendered)

    def test_enforce_command_passes_with_low_or_info_only(self) -> None:
        payload = {
            "items": [
                {"severity": "info", "category": "docs", "summary": "nit"},
                {"severity": "low", "category": "quality", "summary": "minor"},
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            priority_file = Path(tmpdir) / "priority.json"
            priority_file.write_text(json.dumps(payload), encoding="utf-8")
            args = argparse.Namespace(priority_file=str(priority_file))
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = self.script.enforce_command(args)
            self.assertEqual(rc, 0)
            self.assertIn("CodeRabbit gate passed", stdout.getvalue())

    def test_count_command_counts_items(self) -> None:
        payload = {"items": [{"severity": "medium"}, {"severity": "high"}]}
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "backlog.json"
            input_file.write_text(json.dumps(payload), encoding="utf-8")
            args = argparse.Namespace(input_file=str(input_file))
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = self.script.count_command(args)
            self.assertEqual(rc, 0)
            self.assertEqual(stdout.getvalue().strip(), "2")

    def test_count_command_returns_zero_for_non_list_items(self) -> None:
        payload = {"items": {"severity": "high"}}
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "backlog.json"
            input_file.write_text(json.dumps(payload), encoding="utf-8")
            args = argparse.Namespace(input_file=str(input_file))
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = self.script.count_command(args)
            self.assertEqual(rc, 0)
            self.assertEqual(stdout.getvalue().strip(), "0")

    def test_collect_command_writes_priority_and_backlog_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            event_path = tmp_root / "event.json"
            output_dir = tmp_root / "out"
            event_path.write_text("{}", encoding="utf-8")
            findings = [
                {"category": "quality", "severity": "medium", "summary": "needs fix"},
                {"category": "docs", "severity": "info", "summary": "nit"},
            ]
            args = argparse.Namespace(
                event_path=str(event_path),
                event_name="pull_request",
                pr_input="",
                repo_input="",
                output_dir=str(output_dir),
            )

            with mock.patch.object(
                self.script, "_resolve_repository", return_value="owner/repo"
            ), mock.patch.object(
                self.script, "_resolve_pr_number", return_value="123"
            ), mock.patch.object(
                self.script, "_collect_findings", return_value=(findings, "abc123")
            ):
                rc = self.script.collect_command(args)

            self.assertEqual(rc, 0)
            priority = json.loads(
                (output_dir / "priority.json").read_text(encoding="utf-8")
            )
            backlog = json.loads(
                (output_dir / "backlog-medium.json").read_text(encoding="utf-8")
            )
            self.assertEqual(priority["repository"], "owner/repo")
            self.assertEqual(priority["pr_number"], 123)
            self.assertEqual(priority["head_sha"], "abc123")
            self.assertEqual(priority["medium_plus_count"], 1)
            self.assertEqual(len(priority["items"]), 2)
            self.assertEqual(len(backlog["items"]), 1)
            self.assertEqual(backlog["items"][0]["severity"], "medium")
            self.assertTrue((output_dir / "triage.md").exists())
            self.assertTrue((output_dir / "backlog-medium.md").exists())


if __name__ == "__main__":
    unittest.main()
