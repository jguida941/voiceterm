"""Unit tests for check_code_shape violation guidance enrichment."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_code_shape.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("check_code_shape_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_code_shape.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckCodeShapeGuidanceTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()
        cls.policy = cls.script.ShapePolicy(
            soft_limit=350,
            hard_limit=650,
            oversize_growth_limit=25,
            hard_lock_growth_limit=0,
        )

    def test_python_violation_guidance_includes_docs_and_audit_directive(self) -> None:
        violation = self.script._violation(
            path=Path("dev/scripts/example.py"),
            reason="crossed_soft_limit",
            guidance="Refactor into smaller modules before crossing the soft limit.",
            policy=self.policy,
            policy_source="language_default:.py",
            base_lines=300,
            current_lines=360,
        )
        self.assertIn("shape audit", violation["guidance"])
        self.assertIn("modularization or consolidation", violation["guidance"])
        self.assertIn("https://peps.python.org/pep-0008/", violation["guidance"])
        self.assertEqual(len(violation["best_practice_refs"]), 2)

    def test_rust_violation_guidance_includes_rust_refs(self) -> None:
        violation = self.script._violation(
            path=Path("rust/src/bin/voiceterm/example.rs"),
            reason="crossed_soft_limit",
            guidance="Refactor into smaller modules before crossing the soft limit.",
            policy=self.policy,
            policy_source="language_default:.rs",
            base_lines=850,
            current_lines=910,
        )
        self.assertIn("https://doc.rust-lang.org/book/", violation["guidance"])
        self.assertIn("https://rust-lang.github.io/api-guidelines/", violation["guidance"])

    def test_missing_file_guidance_skips_audit_directive(self) -> None:
        violation = self.script._violation(
            path=Path("dev/scripts/example.py"),
            reason="current_file_missing",
            guidance="File is missing in current tree; rerun after resolving rename/delete state.",
            policy=self.policy,
            policy_source="language_default:.py",
            base_lines=20,
            current_lines=0,
        )
        self.assertNotIn("shape audit", violation["guidance"])
