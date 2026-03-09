"""Tests for check_python_subprocess_policy guard script."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import init_temp_repo_root, load_repo_module

SCRIPT = load_repo_module(
    "check_python_subprocess_policy",
    "dev/scripts/checks/check_python_subprocess_policy.py",
)


class CheckPythonSubprocessPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_temp_repo_root(
            self, "dev/scripts", "app/operator_console"
        )

    def _write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_build_report_passes_when_calls_use_explicit_check(self) -> None:
        self._write(
            "dev/scripts/example.py",
            (
                "import subprocess as sp\n"
                "from subprocess import run as subprocess_run\n\n"
                "sp.run(['git', 'status'], check=False)\n"
                "subprocess_run(['git', 'rev-parse'], check=True)\n"
            ),
        )

        report = SCRIPT.build_report(repo_root=self.root)

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["subprocess_run_calls"], 2)
        self.assertEqual(report["violations"], [])

    def test_build_report_fails_when_check_keyword_is_missing(self) -> None:
        path = self._write(
            "app/operator_console/repo_state.py",
            (
                "import subprocess\n\n"
                "def sample() -> int:\n"
                "    result = subprocess.run(['git', 'status'], capture_output=True)\n"
                "    return result.returncode\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            mode="commit-range",
            since_ref="origin/develop",
            head_ref="HEAD",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"],
            [
                {
                    "path": "app/operator_console/repo_state.py",
                    "line": 4,
                    "reason": "subprocess.run call is missing explicit check=",
                }
            ],
        )

    def test_build_report_ignores_test_files(self) -> None:
        self._write(
            "dev/scripts/devctl/tests/test_guard_policy.py",
            (
                "import subprocess\n"
                "subprocess.run(['python3', '--version'])\n"
            ),
        )

        report = SCRIPT.build_report(repo_root=self.root)

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["files_scanned"], 0)
        self.assertEqual(report["files_skipped_tests"], 1)


if __name__ == "__main__":
    unittest.main()
