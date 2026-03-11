"""Tests for script catalog integrity."""

from __future__ import annotations

import unittest

from dev.scripts.devctl import script_catalog


class ScriptCatalogTests(unittest.TestCase):
    """Protect canonical check-script registry integrity."""

    def test_all_catalog_paths_exist(self) -> None:
        for name in script_catalog.CHECK_SCRIPT_FILES:
            path = script_catalog.check_script_path(name)
            self.assertTrue(path.is_file(), f"missing script path for {name}: {path}")

    def test_check_script_files_have_unique_filenames(self) -> None:
        filenames = list(script_catalog.CHECK_SCRIPT_FILES.values())
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_all_probe_catalog_paths_exist(self) -> None:
        for relative in script_catalog.PROBE_SCRIPT_RELATIVE_PATHS.values():
            path = script_catalog.REPO_ROOT / relative
            self.assertTrue(path.is_file(), f"missing probe script path: {path}")

    def test_probe_script_files_have_unique_filenames(self) -> None:
        filenames = list(script_catalog.PROBE_SCRIPT_FILES.values())
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_legacy_rewrite_targets_match_relative_paths(self) -> None:
        expected_targets = set(script_catalog.CHECK_SCRIPT_RELATIVE_PATHS.values())
        rewrite_targets = set(script_catalog.LEGACY_CHECK_SCRIPT_REWRITES.values())
        self.assertEqual(rewrite_targets, expected_targets)


if __name__ == "__main__":
    unittest.main()
