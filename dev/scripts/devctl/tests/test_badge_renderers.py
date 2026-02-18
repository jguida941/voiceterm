"""Tests for CI/mutation badge renderer scripts."""

import importlib.util
import unittest
from pathlib import Path


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


class BadgeRendererTests(unittest.TestCase):
    """Protect pass/fail color semantics for README endpoint badges."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.ci_badge = load_module("render_ci_badge", "dev/scripts/render_ci_badge.py")
        cls.mutation_badge = load_module(
            "render_mutation_badge",
            "dev/scripts/render_mutation_badge.py",
        )

    def test_ci_badge_pass_status_maps_to_black(self) -> None:
        normalized = self.ci_badge.normalize_status("success")
        self.assertEqual(normalized, "passing")
        self.assertEqual(self.ci_badge.color_for_status(normalized), "black")

    def test_ci_badge_non_pass_status_maps_to_red(self) -> None:
        normalized = self.ci_badge.normalize_status("failure")
        self.assertEqual(normalized, "failing")
        self.assertEqual(self.ci_badge.color_for_status(normalized), "red")

    def test_mutation_badge_threshold_maps_to_black_red(self) -> None:
        self.assertEqual(self.mutation_badge.color_for_score(0.80), "black")
        self.assertEqual(self.mutation_badge.color_for_score(0.79), "red")


if __name__ == "__main__":
    unittest.main()
