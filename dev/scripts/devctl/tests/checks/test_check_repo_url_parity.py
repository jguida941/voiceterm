"""Tests for check_repo_url_parity guard script."""

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.checks.script_loader_support import (
    load_module_from_repo_path,
)

REPO_ROOT = Path(__file__).resolve().parents[5]


class CheckRepoUrlParityTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module_from_repo_path(
            module_name="check_repo_url_parity",
            repo_root=REPO_ROOT,
            relative_path="dev/scripts/checks/check_repo_url_parity.py",
        )

    def test_build_report_runs(self) -> None:
        report = self.script.build_report()
        self.assertIsInstance(report, dict)

    def test_report_has_expected_keys(self) -> None:
        report = self.script.build_report()
        for key in ("command", "timestamp", "ok", "violations"):
            self.assertIn(key, report)
        self.assertEqual(report["command"], "check_repo_url_parity")

    def test_canonical_url_constant(self) -> None:
        self.assertEqual(
            self.script.CANONICAL_URL,
            "github.com/jguida941/voiceterm",
        )


if __name__ == "__main__":
    unittest.main()
