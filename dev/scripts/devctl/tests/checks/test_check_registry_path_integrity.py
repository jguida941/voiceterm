"""Tests for script registry path integrity guard."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dev.scripts.checks.check_registry_path_integrity import build_report
from dev.scripts.devctl import script_catalog


class CheckRegistryPathIntegrityTests(unittest.TestCase):
    def test_current_repo_registry_is_clean(self) -> None:
        report = build_report()

        self.assertTrue(report["ok"], report["violations"])

    def test_missing_registered_path_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            report = build_report(
                repo_root=root,
                check_paths={"missing_guard": "dev/scripts/checks/check_missing.py"},
                probe_paths={},
            )

        self.assertFalse(report["ok"])
        self.assertTrue(
            any(
                violation["check"] == "registered_path_exists"
                and violation["script_id"] == "missing_guard"
                for violation in report["violations"]
            )
        )

    def test_unregistered_top_level_probe_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checks_dir = root / "dev/scripts/checks"
            checks_dir.mkdir(parents=True)
            (checks_dir / "probe_unregistered.py").write_text(
                "def main(): return 0\n",
                encoding="utf-8",
            )
            report = build_report(repo_root=root, check_paths={}, probe_paths={})

        self.assertFalse(report["ok"])
        self.assertTrue(
            any(
                violation["check"] == "top_level_entrypoint_registered"
                and violation["script_id"] == "probe_unregistered"
                for violation in report["violations"]
            )
        )

    def test_event_field_probe_is_registered(self) -> None:
        self.assertIn(
            "probe_event_field_naming_consistency",
            script_catalog.PROBE_SCRIPT_FILES,
        )
        self.assertEqual(
            script_catalog.probe_script_relative_path(
                "probe_event_field_naming_consistency"
            ),
            "dev/scripts/checks/probe_event_field_naming_consistency.py",
        )


if __name__ == "__main__":
    unittest.main()
