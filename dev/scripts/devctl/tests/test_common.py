"""Tests for shared devctl command helpers."""

import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl import common
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

    @patch("dev.scripts.devctl.common._run_with_live_output", side_effect=KeyboardInterrupt)
    def test_run_cmd_interrupt_returns_structured_error(self, _run_mock) -> None:
        result = run_cmd("interrupt", [sys.executable, "-c", "print('x')"])
        self.assertEqual(result["returncode"], 130)
        self.assertIn("interrupted", result.get("error", ""))


class RunWithLiveOutputTests(TestCase):
    @patch("dev.scripts.devctl.common._terminate_subprocess_tree")
    @patch("dev.scripts.devctl.common.subprocess.Popen")
    def test_interrupt_terminates_subprocess_tree(
        self,
        popen_mock,
        terminate_mock,
    ) -> None:
        class InterruptingStdout:
            def __iter__(self):
                return self

            def __next__(self):
                raise KeyboardInterrupt

            def close(self):
                return None

        process = SimpleNamespace(
            stdout=InterruptingStdout(),
            wait=lambda timeout=None: 0,
            poll=lambda: None,
            pid=4242,
        )
        popen_mock.return_value = process

        with self.assertRaises(KeyboardInterrupt):
            common._run_with_live_output([sys.executable, "-c", "print('x')"], cwd=None, env=None)

        terminate_mock.assert_called_once_with(process)


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
