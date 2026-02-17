"""Regression tests for Homebrew model-path detection in startup scripts."""

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


class HomebrewModelPathDetectionTests(unittest.TestCase):
    """Ensure Homebrew opt installs keep stable model-cache behavior."""

    def test_start_script_detects_opt_prefixes(self) -> None:
        text = _read("scripts/start.sh")
        self.assertIn("/opt/homebrew/opt/*", text)
        self.assertIn("/usr/local/opt/*", text)

    def test_setup_script_detects_opt_prefixes(self) -> None:
        text = _read("scripts/setup.sh")
        self.assertIn("/opt/homebrew/opt/*", text)
        self.assertIn("/usr/local/opt/*", text)

    def test_scripts_use_physical_paths_for_detection(self) -> None:
        self.assertIn("pwd -P", _read("scripts/start.sh"))
        self.assertIn("pwd -P", _read("scripts/setup.sh"))


if __name__ == "__main__":
    unittest.main()
