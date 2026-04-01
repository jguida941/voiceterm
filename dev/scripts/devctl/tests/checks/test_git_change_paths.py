"""Tests for compatibility-aware baseline mapping in git_change_paths."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.tests.conftest import load_repo_module

SCRIPT = load_repo_module(
    "git_change_paths_script",
    "dev/scripts/checks/git_change_paths.py",
)


def _result(
    *,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class GitChangePathsTests(unittest.TestCase):
    def test_maps_new_package_target_back_to_stable_wrapper_path(self) -> None:
        target = Path("dev/scripts/checks/code_shape/check_code_shape.py")
        wrapper = Path("dev/scripts/checks/check_code_shape.py")

        def run_git(args: list[str], *, check: bool = True):
            if args == [
                "git",
                "diff",
                "--name-status",
                "--find-renames=50%",
                "--diff-filter=ACMR",
                "HEAD",
            ]:
                return _result(stdout=f"M\t{wrapper.as_posix()}\n")
            if args == ["git", "ls-files", "--others", "--exclude-standard"]:
                return _result(stdout=f"{target.as_posix()}\n")
            if args == ["git", "rev-parse", "--show-toplevel"]:
                return _result(stdout="/tmp/repo\n")
            if args == ["git", "cat-file", "-e", f"HEAD:{target.as_posix()}"]:
                return _result(returncode=128, stderr="missing")
            if args == ["git", "cat-file", "-e", f"HEAD:{wrapper.as_posix()}"]:
                return _result()
            raise AssertionError(f"unexpected git args: {args}")

        redirects = [
            {
                "path": wrapper.as_posix(),
                "target": target.as_posix(),
                "resolved_target": target.as_posix(),
            }
        ]
        with patch.object(SCRIPT, "collect_compatibility_redirects", return_value=redirects):
            changed, base_map = SCRIPT.list_changed_paths_with_base_map(
                run_git,
                None,
                "HEAD",
            )

        self.assertEqual(changed, sorted([wrapper, target]))
        self.assertEqual(base_map[wrapper], wrapper)
        self.assertEqual(base_map[target], wrapper)

    def test_keeps_identity_mapping_when_target_already_exists_at_base_ref(self) -> None:
        target = Path("dev/scripts/checks/code_shape/check_code_shape.py")
        wrapper = Path("dev/scripts/checks/check_code_shape.py")

        def run_git(args: list[str], *, check: bool = True):
            if args == [
                "git",
                "diff",
                "--name-status",
                "--find-renames=50%",
                "--diff-filter=ACMR",
                "HEAD",
            ]:
                return _result(stdout=f"M\t{target.as_posix()}\n")
            if args == ["git", "ls-files", "--others", "--exclude-standard"]:
                return _result()
            if args == ["git", "rev-parse", "--show-toplevel"]:
                return _result(stdout="/tmp/repo\n")
            if args == ["git", "cat-file", "-e", f"HEAD:{target.as_posix()}"]:
                return _result()
            raise AssertionError(f"unexpected git args: {args}")

        redirects = [
            {
                "path": wrapper.as_posix(),
                "target": target.as_posix(),
                "resolved_target": target.as_posix(),
            }
        ]
        with patch.object(SCRIPT, "collect_compatibility_redirects", return_value=redirects):
            changed, base_map = SCRIPT.list_changed_paths_with_base_map(
                run_git,
                None,
                "HEAD",
            )

        self.assertEqual(changed, [target])
        self.assertEqual(base_map[target], target)
