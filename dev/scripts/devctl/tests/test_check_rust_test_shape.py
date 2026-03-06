"""Unit tests for Rust test-file shape guard policy behavior."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_rust_test_shape.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("check_rust_test_shape_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_rust_test_shape.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckRustTestShapeTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def test_policy_override_applies_for_known_hotspot(self) -> None:
        policy, source = self.script._policy_for_path(
            Path("rust/src/bin/voiceterm/event_loop/tests.rs")
        )
        self.assertTrue(source.startswith("path_override:"))
        self.assertEqual(policy.soft_limit, 6200)
        self.assertEqual(policy.hard_limit, 7000)

    def test_evaluate_crosses_soft_limit(self) -> None:
        policy = self.script.TestShapePolicy(
            soft_limit=100,
            hard_limit=200,
            oversize_growth_limit=20,
            hard_lock_growth_limit=0,
        )
        reason = self.script._evaluate(base_lines=90, current_lines=110, policy=policy)
        self.assertEqual(reason, "crossed_soft_limit")

    def test_evaluate_enforces_oversize_growth_lock(self) -> None:
        policy = self.script.TestShapePolicy(
            soft_limit=100,
            hard_limit=200,
            oversize_growth_limit=10,
            hard_lock_growth_limit=0,
        )
        reason = self.script._evaluate(base_lines=150, current_lines=165, policy=policy)
        self.assertEqual(reason, "exceeded_oversize_growth_limit")

    def test_count_lines_handles_none(self) -> None:
        self.assertEqual(self.script._count_lines(None), 0)
        self.assertEqual(self.script._count_lines("a\nb\n"), 2)

    def test_is_test_path_accepts_suffix_tests_rs(self) -> None:
        self.assertTrue(
            self.script._is_test_path(Path("rust/src/bin/voiceterm/foo_tests.rs"))
        )
