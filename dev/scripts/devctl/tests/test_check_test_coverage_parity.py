"""Tests for check_test_coverage_parity guard script."""

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def load_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckTestCoverageParityTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "check_test_coverage_parity",
            "dev/scripts/checks/check_test_coverage_parity.py",
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
