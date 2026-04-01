"""Tests for check_test_coverage_parity guard script."""

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.checks.script_loader_support import (
    load_module_from_repo_path,
)

REPO_ROOT = Path(__file__).resolve().parents[5]


class CheckTestCoverageParityTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module_from_repo_path(
            module_name="check_test_coverage_parity",
            repo_root=REPO_ROOT,
            relative_path="dev/scripts/checks/check_test_coverage_parity.py",
        )

    def test_build_report_runs(self) -> None:
        report = self.script.build_report()
        self.assertIsInstance(report, dict)

    def test_report_has_expected_keys(self) -> None:
        report = self.script.build_report()
        for key in ("command", "timestamp", "ok", "violations"):
            self.assertIn(key, report, f"missing key: {key}")
        self.assertEqual(report["command"], "check_test_coverage_parity")
        self.assertIsInstance(report["violations"], list)


if __name__ == "__main__":
    unittest.main()
