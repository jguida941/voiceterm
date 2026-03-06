"""Tests for check_repo_url_parity guard script."""

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


class CheckRepoUrlParityTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "check_repo_url_parity",
            "dev/scripts/checks/check_repo_url_parity.py",
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
