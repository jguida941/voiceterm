"""Tests for release version parity check script helpers."""

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[4]


def load_module(name: str, relative_path: str):
    """Load a repository script as a module for unit tests."""
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseVersionParityScriptTests(unittest.TestCase):
    """Protect expected-version parity behavior used by release workflows."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "check_release_version_parity",
            "dev/scripts/checks/check_release_version_parity.py",
        )

    def test_build_report_expected_version_match_true(self) -> None:
        with mock.patch.object(
            self.script, "_read_cargo_version", return_value="1.2.3"
        ), mock.patch.object(
            self.script, "_read_pyproject_version", return_value="1.2.3"
        ), mock.patch.object(
            self.script, "_read_init_version", return_value="1.2.3"
        ), mock.patch.object(
            self.script, "_read_plist_versions", return_value=("1.2.3", "1.2.3")
        ):
            report = self.script._build_report(expected_version="1.2.3")

        self.assertTrue(report["ok"])
        self.assertTrue(report["expected_version_match"])
        self.assertEqual(report["versions_present"], ["1.2.3"])

    def test_build_report_expected_version_mismatch_false(self) -> None:
        with mock.patch.object(
            self.script, "_read_cargo_version", return_value="1.2.3"
        ), mock.patch.object(
            self.script, "_read_pyproject_version", return_value="1.2.3"
        ), mock.patch.object(
            self.script, "_read_init_version", return_value="1.2.3"
        ), mock.patch.object(
            self.script, "_read_plist_versions", return_value=("1.2.3", "1.2.3")
        ):
            report = self.script._build_report(expected_version="9.9.9")

        self.assertFalse(report["ok"])
        self.assertFalse(report["expected_version_match"])
        self.assertEqual(report["versions_present"], ["1.2.3"])


if __name__ == "__main__":
    unittest.main()
