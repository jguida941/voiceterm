"""Unit tests for check_code_shape violation guidance enrichment."""

from __future__ import annotations

import importlib.util
from datetime import date
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

    def test_evaluate_shape_new_file_exceeds_soft_limit(self) -> None:
        violation = self.script._evaluate_shape(
            path=Path("dev/scripts/new_tool.py"),
            policy=self.policy,
            policy_source="language_default:.py",
            base_lines=None,
            current_lines=400,
        )
        self.assertIsNotNone(violation)
        self.assertEqual(violation["reason"], "new_file_exceeds_soft_limit")

    def test_evaluate_shape_crossed_soft_limit(self) -> None:
        violation = self.script._evaluate_shape(
            path=Path("dev/scripts/example.py"),
            policy=self.policy,
            policy_source="language_default:.py",
            base_lines=340,
            current_lines=351,
        )
        self.assertIsNotNone(violation)
        self.assertEqual(violation["reason"], "crossed_soft_limit")

    def test_evaluate_shape_crossed_hard_limit(self) -> None:
        violation = self.script._evaluate_shape(
            path=Path("dev/scripts/example.py"),
            policy=self.policy,
            policy_source="language_default:.py",
            base_lines=645,
            current_lines=651,
        )
        self.assertIsNotNone(violation)
        self.assertEqual(violation["reason"], "crossed_hard_limit")

    def test_evaluate_shape_hard_locked_file_grew(self) -> None:
        violation = self.script._evaluate_shape(
            path=Path("dev/scripts/example.py"),
            policy=self.policy,
            policy_source="language_default:.py",
            base_lines=700,
            current_lines=701,
        )
        self.assertIsNotNone(violation)
        self.assertEqual(violation["reason"], "hard_locked_file_grew")

    def test_evaluate_shape_oversize_growth_budget(self) -> None:
        oversize = self.script.ShapePolicy(
            soft_limit=350,
            hard_limit=650,
            oversize_growth_limit=10,
            hard_lock_growth_limit=10,
        )
        violation = self.script._evaluate_shape(
            path=Path("dev/scripts/example.py"),
            policy=oversize,
            policy_source="language_default:.py",
            base_lines=400,
            current_lines=412,
        )
        self.assertIsNotNone(violation)
        self.assertEqual(violation["reason"], "oversize_file_growth_exceeded_budget")

    def test_evaluate_shape_returns_none_when_within_budget(self) -> None:
        violation = self.script._evaluate_shape(
            path=Path("dev/scripts/example.py"),
            policy=self.policy,
            policy_source="language_default:.py",
            base_lines=200,
            current_lines=210,
        )
        self.assertIsNone(violation)

    def test_evaluate_absolute_shape_flags_hard_limit(self) -> None:
        violation = self.script._evaluate_absolute_shape(
            path=Path("dev/scripts/example.py"),
            policy=self.policy,
            policy_source="language_default:.py",
            current_lines=900,
        )
        self.assertIsNotNone(violation)
        self.assertEqual(violation["reason"], "absolute_hard_limit_exceeded")

    def test_evaluate_stale_path_override_flags_loose_override(self) -> None:
        override = self.script.ShapePolicy(
            soft_limit=1200,
            hard_limit=1500,
            oversize_growth_limit=0,
            hard_lock_growth_limit=0,
        )
        language_default = self.script.ShapePolicy(
            soft_limit=900,
            hard_limit=1400,
            oversize_growth_limit=40,
            hard_lock_growth_limit=0,
        )
        violation = self.script._evaluate_stale_path_override(
            path=Path("rust/src/bin/voiceterm/example.rs"),
            override_policy=override,
            language_default_policy=language_default,
            policy_source="path_override:rust/src/bin/voiceterm/example.rs",
            current_lines=555,
            review_window_days=30,
            review_window_line_counts=[555, 560, 575],
        )
        self.assertIsNotNone(violation)
        self.assertEqual(violation["reason"], "stale_path_override_below_default_soft_limit")

    def test_evaluate_stale_path_override_skips_when_recent_history_exceeds_default(self) -> None:
        override = self.script.ShapePolicy(
            soft_limit=1200,
            hard_limit=1500,
            oversize_growth_limit=0,
            hard_lock_growth_limit=0,
        )
        language_default = self.script.ShapePolicy(
            soft_limit=900,
            hard_limit=1400,
            oversize_growth_limit=40,
            hard_lock_growth_limit=0,
        )
        violation = self.script._evaluate_stale_path_override(
            path=Path("rust/src/bin/voiceterm/example.rs"),
            override_policy=override,
            language_default_policy=language_default,
            policy_source="path_override:rust/src/bin/voiceterm/example.rs",
            current_lines=555,
            review_window_days=30,
            review_window_line_counts=[555, 910],
        )
        self.assertIsNone(violation)

    def test_evaluate_stale_path_override_skips_when_override_is_not_looser(self) -> None:
        override = self.script.ShapePolicy(
            soft_limit=750,
            hard_limit=950,
            oversize_growth_limit=0,
            hard_lock_growth_limit=0,
        )
        language_default = self.script.ShapePolicy(
            soft_limit=900,
            hard_limit=1400,
            oversize_growth_limit=40,
            hard_lock_growth_limit=0,
        )
        violation = self.script._evaluate_stale_path_override(
            path=Path("rust/src/bin/voiceterm/example.rs"),
            override_policy=override,
            language_default_policy=language_default,
            policy_source="path_override:rust/src/bin/voiceterm/example.rs",
            current_lines=555,
            review_window_days=30,
            review_window_line_counts=[555, 560],
        )
        self.assertIsNone(violation)

    def test_scan_rust_functions_reports_name_and_line_range(self) -> None:
        source = "\n".join(
            [
                "fn alpha() {",
                "    let _ = 1;",
                "}",
                "",
                "fn beta() {",
                "    let _ = 2;",
                "    let _ = 3;",
                "}",
            ]
        )
        functions = self.script._scan_rust_functions(source)
        self.assertEqual([item["name"] for item in functions], ["alpha", "beta"])
        self.assertEqual(functions[0]["line_count"], 3)
        self.assertEqual(functions[1]["line_count"], 4)

    def test_should_skip_test_path_true_without_override_policy(self) -> None:
        should_skip = self.script._should_skip_test_path(
            Path("rust/src/bin/voiceterm/event_loop/tests.rs"),
            "language_default:.rs",
        )
        self.assertTrue(should_skip)

    def test_should_skip_test_path_false_with_path_override_policy(self) -> None:
        should_skip = self.script._should_skip_test_path(
            Path("rust/src/bin/voiceterm/event_loop/tests.rs"),
            "path_override:rust/src/bin/voiceterm/event_loop/tests.rs",
        )
        self.assertFalse(should_skip)

    def test_evaluate_function_shape_flags_oversized_function_without_exception(self) -> None:
        source = "\n".join(
            ["fn oversized() {"]
            + ["    let _value = 1;"] * 8
            + ["}"]
        )
        policy = self.script.FunctionShapePolicy(max_lines=5)
        violations, exceptions_used = self.script._evaluate_function_shape(
            path=Path("rust/src/bin/voiceterm/example.rs"),
            policy=policy,
            policy_source="function_path_override:rust/src/bin/voiceterm/example.rs",
            text=source,
            today=date(2026, 3, 4),
        )
        self.assertEqual(exceptions_used, 0)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["reason"], "function_exceeds_max_lines")
        self.assertEqual(violations[0]["function_name"], "oversized")

    def test_evaluate_function_shape_honors_active_exception_budget(self) -> None:
        source = "\n".join(
            ["pub(super) fn dispatch_message(&mut self) -> bool {"]
            + ["    let _value = 1;"] * 250
            + ["    true", "}"]
        )
        policy = self.script.FunctionShapePolicy(max_lines=220)
        violations, exceptions_used = self.script._evaluate_function_shape(
            path=Path("rust/src/bin/voiceterm/writer/state/dispatch.rs"),
            policy=policy,
            policy_source="function_path_override:rust/src/bin/voiceterm/writer/state/dispatch.rs",
            text=source,
            today=date(2026, 3, 4),
        )
        self.assertEqual(exceptions_used, 1)
        self.assertEqual(violations, [])
