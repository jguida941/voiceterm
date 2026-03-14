"""Tests for check_command_source_validation guard script."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import (
    init_temp_repo_root,
    load_repo_module,
    override_module_attrs,
)

SCRIPT = load_repo_module(
    "check_command_source_validation",
    "dev/scripts/checks/package_layout/check_command_source_validation.py",
)


class CheckCommandSourceValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_temp_repo_root(self, "scripts", "pypi/src")
        override_module_attrs(
            self,
            SCRIPT,
            TARGET_ROOTS=(Path("scripts"), Path("pypi/src")),
        )

    def _write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_build_report_flags_shlex_split_of_cli_input(self) -> None:
        path = self._write(
            "scripts/python_fallback.py",
            (
                "import shlex\n\n"
                "def main(args):\n"
                "    return shlex.split(args.codex_args)\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            scan_context=SCRIPT.ScanContext(
                mode="commit-range",
                since_ref="origin/develop",
                head_ref="HEAD",
            ),
        )

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"],
            [
                {
                    "path": "scripts/python_fallback.py",
                    "line": 4,
                    "reason": "shlex.split() on CLI/env/config input requires structured args or validation",
                }
            ],
        )

    def test_build_report_flags_env_controlled_command_values(self) -> None:
        path = self._write(
            "pypi/src/voiceterm/cli.py",
            (
                "import os\n"
                "import subprocess\n\n"
                "def _run(cmd):\n"
                "    return subprocess.run(cmd, check=False)\n\n"
                "def main():\n"
                "    repo_url = os.environ.get('VOICETERM_REPO_URL', 'https://github.com/acme/repo')\n"
                "    _run(['git', 'clone', repo_url])\n"
            ),
        )

        report = SCRIPT.build_report(repo_root=self.root, candidate_paths=[path.relative_to(self.root)])

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"],
            [
                {
                    "path": "pypi/src/voiceterm/cli.py",
                    "line": 9,
                    "reason": "command argv uses env-controlled values without validation",
                }
            ],
        )

    def test_build_report_flags_raw_sys_argv_forwarding(self) -> None:
        path = self._write(
            "pypi/src/voiceterm/launcher.py",
            (
                "import subprocess\n"
                "import sys\n\n"
                "def main():\n"
                "    return subprocess.run(['voiceterm', *sys.argv[1:]], check=False)\n"
            ),
        )

        report = SCRIPT.build_report(repo_root=self.root, candidate_paths=[path.relative_to(self.root)])

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"],
            [
                {
                    "path": "pypi/src/voiceterm/launcher.py",
                    "line": 5,
                    "reason": "command argv forwards sys.argv without validation",
                }
            ],
        )

    def test_build_report_accepts_validated_wrappers(self) -> None:
        path = self._write(
            "pypi/src/voiceterm/validated.py",
            (
                "import os\n"
                "import subprocess\n"
                "import sys\n\n"
                "def _validated_repo_url(raw):\n"
                "    return raw.strip()\n\n"
                "def _validated_forward_args(argv):\n"
                "    return list(argv)\n\n"
                "def _run(cmd):\n"
                "    return subprocess.run(cmd, check=False)\n\n"
                "def main():\n"
                "    repo_url = _validated_repo_url(os.environ.get('VOICETERM_REPO_URL', 'https://github.com/acme/repo'))\n"
                "    forwarded = _validated_forward_args(sys.argv[1:])\n"
                "    _run(['git', 'clone', repo_url])\n"
                "    return subprocess.run(['voiceterm', *forwarded], check=False)\n"
            ),
        )

        report = SCRIPT.build_report(repo_root=self.root, candidate_paths=[path.relative_to(self.root)])

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["violations"], [])

    def test_build_report_ignores_test_files(self) -> None:
        self._write(
            "scripts/tests/test_launcher.py",
            (
                "import subprocess\n"
                "import sys\n"
                "subprocess.run(['voiceterm', *sys.argv[1:]], check=False)\n"
            ),
        )

        report = SCRIPT.build_report(repo_root=self.root)

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["files_scanned"], 0)
        self.assertEqual(report["files_skipped_tests"], 1)


if __name__ == "__main__":
    unittest.main()
