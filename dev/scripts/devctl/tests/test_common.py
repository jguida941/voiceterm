"""Tests for shared devctl command helpers."""

import sys
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.common import run_cmd
from dev.scripts.devctl.steps import format_steps_md


class RunCmdTests(TestCase):
    @patch("builtins.print")
    def test_run_cmd_success_has_no_failure_output(self, _mock_print) -> None:
        result = run_cmd("ok", [sys.executable, "-c", "print('ok')"])
        self.assertEqual(result["returncode"], 0)
        self.assertNotIn("failure_output", result)

    @patch("builtins.print")
    def test_run_cmd_failure_keeps_bounded_output_excerpt(self, _mock_print) -> None:
        script = "\n".join(
            [
                "import sys",
                "print('line-1')",
                "print('line-2')",
                "print('line-3')",
                "sys.exit(3)",
            ]
        )
        result = run_cmd("fail", [sys.executable, "-c", script])
        self.assertEqual(result["returncode"], 3)
        self.assertIn("line-3", result.get("failure_output", ""))

    def test_run_cmd_missing_binary_returns_structured_error(self) -> None:
        result = run_cmd("missing", ["definitely-missing-devctl-test-binary"])
        self.assertEqual(result["returncode"], 127)
        self.assertIn("error", result)


class FormatStepsMarkdownTests(TestCase):
    def test_format_steps_md_includes_failure_output_section(self) -> None:
        markdown = format_steps_md(
            [
                {
                    "name": "fmt-check",
                    "returncode": 0,
                    "duration_s": 0.7,
                    "cmd": ["cargo", "fmt", "--check"],
                },
                {
                    "name": "clippy",
                    "returncode": 1,
                    "duration_s": 12.3,
                    "cmd": ["cargo", "clippy"],
                    "failure_output": "warning: unused variable",
                },
            ]
        )
        self.assertIn("## Failure Output", markdown)
        self.assertIn("`clippy`", markdown)
        self.assertIn("warning: unused variable", markdown)
