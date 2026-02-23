"""Unit tests for CodeRabbit Ralph loop core helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/coderabbit_ralph_loop_core.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("coderabbit_ralph_loop_core_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load coderabbit_ralph_loop_core.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CodeRabbitRalphLoopCoreTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _call_run_fix(self, command: str):
        return self.script.run_fix_command(
            command,
            attempt=2,
            repo="owner/repo",
            branch="develop",
            backlog_count=3,
            backlog_dir=Path("/tmp/ralph-backlog"),
            run_id=42,
            run_sha="a" * 40,
        )

    def test_run_fix_command_rejects_invalid_quoted_command(self) -> None:
        rc, error = self._call_run_fix("\"unterminated")
        self.assertEqual(rc, 2)
        self.assertIsNotNone(error)
        self.assertIn("invalid --fix-command", error or "")

    def test_run_fix_command_rejects_empty_command(self) -> None:
        rc, error = self._call_run_fix("   ")
        self.assertEqual(rc, 2)
        self.assertEqual(error, "invalid --fix-command: empty command")

    def test_run_fix_command_uses_argument_vector_without_shell(self) -> None:
        with patch.object(self.script.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run_mock:
            rc, error = self._call_run_fix("python3 dev/scripts/devctl.py check --profile ci")

        self.assertEqual(rc, 0)
        self.assertIsNone(error)
        run_mock.assert_called_once()
        args, kwargs = run_mock.call_args
        self.assertEqual(
            args[0],
            ["python3", "dev/scripts/devctl.py", "check", "--profile", "ci"],
        )
        self.assertEqual(kwargs["cwd"], self.script.REPO_ROOT)
        self.assertFalse(kwargs["check"])
        self.assertNotIn("shell", kwargs)
        env = kwargs["env"]
        self.assertEqual(env["RALPH_ATTEMPT"], "2")
        self.assertEqual(env["RALPH_REPO"], "owner/repo")
        self.assertEqual(env["RALPH_BRANCH"], "develop")
        self.assertEqual(env["RALPH_BACKLOG_COUNT"], "3")
        self.assertEqual(env["RALPH_BACKLOG_DIR"], "/tmp/ralph-backlog")
        self.assertEqual(env["RALPH_SOURCE_RUN_ID"], "42")
        self.assertEqual(env["RALPH_SOURCE_SHA"], "a" * 40)
