"""Tests for check_bundle_registry_dry guard script."""

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


class CheckBundleRegistryDryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "check_bundle_registry_dry",
            "dev/scripts/checks/check_bundle_registry_dry.py",
        )

    def test_build_report_returns_ok(self) -> None:
        report = self.script.build_report()
        self.assertTrue(report["ok"])

    def test_report_has_expected_keys(self) -> None:
        report = self.script.build_report()
        for key in ("command", "timestamp", "ok", "violations"):
            self.assertIn(key, report)
        self.assertEqual(report["command"], "check_bundle_registry_dry")

    def test_report_uses_composition_flag(self) -> None:
        report = self.script.build_report()
        self.assertTrue(report["uses_composition"])

    def test_render_markdown_contains_header(self) -> None:
        report = self.script.build_report()
        md = self.script.render_markdown(report)
        self.assertIn("# check_bundle_registry_dry", md)


if __name__ == "__main__":
    unittest.main()
