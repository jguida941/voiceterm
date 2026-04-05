"""Tests for the governed commit gate (AUD-27).

Validates:
- Pre-commit hook template exists and is executable
- Commit command module imports cleanly
- Commit is blocked when guards return non-zero
- Commit proceeds when guards return zero
- Git commit args are built correctly from parsed arguments
"""

from __future__ import annotations

import os
import stat
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dev.scripts.devctl.commands.vcs.commit import (
    _build_git_commit_cmd,
    _run_guard_bundle,
    run_commit,
)
from dev.scripts.devctl.config import REPO_ROOT


def _make_args(**overrides) -> SimpleNamespace:
    """Build a minimal args namespace for commit tests."""
    defaults = {
        "message": "test commit",
        "amend": False,
        "passthrough": [],
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_subprocess_result(returncode: int, stdout: str = "", stderr: str = ""):
    """Create a mock subprocess.CompletedProcess."""
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestPreCommitHookTemplate(unittest.TestCase):
    """Verify the pre-commit hook template file."""

    HOOK_PATH = REPO_ROOT / "dev/config/templates/portable_governance_pre_commit_hook.sh"

    def test_hook_template_exists(self):
        self.assertTrue(
            self.HOOK_PATH.exists(),
            f"Pre-commit hook template missing at {self.HOOK_PATH}",
        )

    def test_hook_template_is_executable(self):
        mode = os.stat(self.HOOK_PATH).st_mode
        self.assertTrue(
            mode & stat.S_IXUSR,
            "Pre-commit hook template must be executable (chmod +x)",
        )

    def test_hook_template_uses_quick_profile(self):
        content = self.HOOK_PATH.read_text()
        self.assertIn("--profile quick", content)
        self.assertNotIn("--profile ci", content)

    def test_hook_template_has_shebang(self):
        content = self.HOOK_PATH.read_text()
        self.assertTrue(
            content.startswith("#!/"),
            "Hook template must start with a shebang line",
        )


class TestCommitModuleImport(unittest.TestCase):
    """Verify the commit module loads without errors."""

    def test_import_run_commit(self):
        from dev.scripts.devctl.commands.vcs.commit import run_commit
        self.assertTrue(callable(run_commit))

    def test_import_run(self):
        from dev.scripts.devctl.commands.vcs.commit import run
        self.assertTrue(callable(run))


class TestBuildGitCommitCmd(unittest.TestCase):
    """Verify git commit command construction from args."""

    def test_message_only(self):
        args = _make_args(message="fix: resolve bug")
        cmd = _build_git_commit_cmd(args)
        self.assertEqual(cmd, ["git", "commit", "-m", "fix: resolve bug"])

    def test_amend(self):
        args = _make_args(message=None, amend=True)
        cmd = _build_git_commit_cmd(args)
        self.assertEqual(cmd, ["git", "commit", "--amend"])

    def test_message_and_amend(self):
        args = _make_args(message="updated msg", amend=True)
        cmd = _build_git_commit_cmd(args)
        self.assertEqual(cmd, ["git", "commit", "-m", "updated msg", "--amend"])

    def test_passthrough_args(self):
        args = _make_args(message="msg", passthrough=["--no-edit", "--allow-empty"])
        cmd = _build_git_commit_cmd(args)
        self.assertEqual(
            cmd,
            ["git", "commit", "-m", "msg", "--no-edit", "--allow-empty"],
        )

    def test_no_message_no_amend(self):
        args = _make_args(message=None, amend=False)
        cmd = _build_git_commit_cmd(args)
        self.assertEqual(cmd, ["git", "commit"])


class TestGuardBundleBlocks(unittest.TestCase):
    """Verify that commit is blocked when guards fail."""

    def test_commit_blocked_on_guard_failure(self):
        guard_runner = MagicMock(return_value=_mock_subprocess_result(1, stderr="FAIL"))
        git_runner = MagicMock(return_value=_mock_subprocess_result(0))
        args = _make_args()

        rc = run_commit(
            args,
            guard_runner=guard_runner,
            git_runner=git_runner,
        )

        self.assertEqual(rc, 1, "Commit must be blocked when guards fail")
        git_runner.assert_not_called()

    def test_guard_failure_reports_blocked_status(self):
        guard_runner = MagicMock(return_value=_mock_subprocess_result(2))
        git_runner = MagicMock(return_value=_mock_subprocess_result(0))
        args = _make_args(format="json")

        rc = run_commit(
            args,
            guard_runner=guard_runner,
            git_runner=git_runner,
        )

        self.assertEqual(rc, 1)
        git_runner.assert_not_called()


class TestGuardBundlePasses(unittest.TestCase):
    """Verify that commit proceeds when guards pass."""

    def test_commit_proceeds_on_guard_success(self):
        guard_runner = MagicMock(return_value=_mock_subprocess_result(0))
        git_runner = MagicMock(return_value=_mock_subprocess_result(0))
        args = _make_args()

        rc = run_commit(
            args,
            guard_runner=guard_runner,
            git_runner=git_runner,
        )

        self.assertEqual(rc, 0, "Commit must succeed when guards pass")
        git_runner.assert_called_once()

    def test_git_commit_failure_propagates(self):
        guard_runner = MagicMock(return_value=_mock_subprocess_result(0))
        git_runner = MagicMock(return_value=_mock_subprocess_result(128))
        args = _make_args()

        rc = run_commit(
            args,
            guard_runner=guard_runner,
            git_runner=git_runner,
        )

        self.assertEqual(rc, 128, "Git commit exit code must propagate")

    def test_git_commit_receives_correct_args(self):
        guard_runner = MagicMock(return_value=_mock_subprocess_result(0))
        git_runner = MagicMock(return_value=_mock_subprocess_result(0))
        args = _make_args(message="feat: add widget")

        run_commit(
            args,
            guard_runner=guard_runner,
            git_runner=git_runner,
        )

        call_args = git_runner.call_args
        cmd = call_args[0][0]
        self.assertEqual(cmd, ["git", "commit", "-m", "feat: add widget"])


class TestGuardBundleRunner(unittest.TestCase):
    """Verify _run_guard_bundle invokes the correct devctl command."""

    def test_guard_bundle_calls_check_quick(self):
        mock_runner = MagicMock(return_value=_mock_subprocess_result(0))
        rc = _run_guard_bundle(runner=mock_runner)

        self.assertEqual(rc, 0)
        call_args = mock_runner.call_args
        cmd = call_args[1].get("cmd") or call_args[0][0]
        cmd_str = " ".join(cmd)
        self.assertIn("check", cmd_str)
        self.assertIn("--profile", cmd_str)
        self.assertIn("quick", cmd_str)


class TestCommitParserEndToEnd(unittest.TestCase):
    """Prove the real CLI parser accepts option-style passthrough args."""

    def test_parser_accepts_option_passthrough_with_separator(self) -> None:
        """devctl commit -m 'test' -- --allow-empty must parse without error."""
        from dev.scripts.devctl.sync_parser import add_commit_parser
        import argparse

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_commit_parser(sub)
        args = parser.parse_args(["commit", "-m", "test", "--", "--allow-empty"])
        self.assertEqual(args.message, "test")
        self.assertIn("--allow-empty", args.passthrough)

    def test_parser_accepts_plain_passthrough(self) -> None:
        """devctl commit -m 'test' -- file.py must parse without error."""
        from dev.scripts.devctl.sync_parser import add_commit_parser
        import argparse

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_commit_parser(sub)
        args = parser.parse_args(["commit", "-m", "test", "--", "file.py"])
        self.assertEqual(args.message, "test")
        self.assertIn("file.py", args.passthrough)


class TestPreCommitHookGuidance(unittest.TestCase):
    """Prove the hook template prints remediation guidance on failure."""

    def test_hook_captures_exit_code_without_errexit(self) -> None:
        """Hook must not use set -e for the guard invocation."""
        hook_path = REPO_ROOT / "dev/config/templates/portable_governance_pre_commit_hook.sh"
        content = hook_path.read_text()
        # Must NOT have set -e (or set -euo) before the guard call
        self.assertNotIn("set -euo", content)
        self.assertNotIn("set -e\n", content)
        # Must capture exit code explicitly
        self.assertIn("|| exit_code=$?", content)


if __name__ == "__main__":
    unittest.main()
