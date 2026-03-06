"""Unit tests for check_rust_lint_debt test-block filtering."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_rust_lint_debt.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("check_rust_lint_debt_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_rust_lint_debt.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckRustLintDebtTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def test_strip_cfg_test_blocks_removes_entire_module(self) -> None:
        text = (
            "fn runtime() { value.unwrap(); }\n"
            "#[cfg(test)]\n"
            "mod tests {\n"
            "    fn nested() { if true { value.expect(\"x\"); } }\n"
            "}\n"
            "fn still_runtime() { #[allow(dead_code)] fn x() {} }\n"
        )
        stripped = self.script._strip_cfg_test_blocks(text)
        self.assertIn("runtime", stripped)
        self.assertIn("still_runtime", stripped)
        self.assertNotIn("mod tests", stripped)
        self.assertNotIn("expect(", stripped)

    def test_count_metrics_ignores_cfg_test_debt(self) -> None:
        text = (
            "#[allow(clippy::too_many_lines)]\n"
            "fn runtime() { value.unwrap(); }\n"
            "#[cfg(test)]\n"
            "mod tests {\n"
            "    #[allow(clippy::unwrap_used)]\n"
            "    fn helper() { value.expect(\"test\"); }\n"
            "}\n"
        )
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["allow_attrs"], 1)
        self.assertEqual(metrics["dead_code_allow_attrs"], 0)
        self.assertEqual(metrics["unwrap_expect_calls"], 1)
        self.assertEqual(metrics["unchecked_unwrap_expect_calls"], 0)
        self.assertEqual(metrics["panic_macro_calls"], 0)

    def test_count_metrics_counts_inner_allow_attributes(self) -> None:
        text = (
            "#![allow(clippy::module_name_repetitions)]\n"
            "#[allow(clippy::too_many_lines)]\n"
            "fn runtime() { value.unwrap(); }\n"
        )
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["allow_attrs"], 2)
        self.assertEqual(metrics["dead_code_allow_attrs"], 0)
        self.assertEqual(metrics["unwrap_expect_calls"], 1)
        self.assertEqual(metrics["unchecked_unwrap_expect_calls"], 0)
        self.assertEqual(metrics["panic_macro_calls"], 0)

    def test_count_metrics_tracks_unchecked_unwrap_and_panic_calls(self) -> None:
        text = (
            "fn runtime() {\n"
            "    let _ = value.unwrap_unchecked();\n"
            "    panic!(\"boom\");\n"
            "    unreachable!(\"impossible\");\n"
            "}\n"
        )
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["unchecked_unwrap_expect_calls"], 1)
        self.assertEqual(metrics["panic_macro_calls"], 1)
        self.assertEqual(metrics["dead_code_allow_attrs"], 0)

    def test_count_metrics_handles_none_input(self) -> None:
        metrics = self.script._count_metrics(None)
        self.assertEqual(metrics["allow_attrs"], 0)
        self.assertEqual(metrics["dead_code_allow_attrs"], 0)
        self.assertEqual(metrics["unwrap_expect_calls"], 0)
        self.assertEqual(metrics["unchecked_unwrap_expect_calls"], 0)
        self.assertEqual(metrics["panic_macro_calls"], 0)

    def test_strip_cfg_test_blocks_handles_cfg_any_test_and_cfg_not_test(self) -> None:
        text = (
            "#[cfg(any(test, feature = \"bench\"))]\n"
            "fn test_only() { value.expect(\"x\"); }\n"
            "#[cfg(not(test))]\n"
            "fn runtime_only() { value.expect(\"runtime\"); }\n"
        )
        stripped = self.script._strip_cfg_test_blocks(text)
        self.assertNotIn("test_only", stripped)
        self.assertIn("runtime_only", stripped)

    def test_collect_dead_code_allow_instances_reports_reason_presence(self) -> None:
        text = (
            "#![allow(dead_code)]\n"
            "#[allow(dead_code, reason = \"staged\")]\n"
            "#[allow(clippy::too_many_lines)]\n"
        )
        instances = self.script._collect_dead_code_allow_instances(text)
        self.assertEqual(len(instances), 2)
        self.assertEqual(instances[0]["line"], 1)
        self.assertFalse(instances[0]["has_reason"])
        self.assertEqual(instances[1]["line"], 2)
        self.assertTrue(instances[1]["has_reason"])

    def test_count_metrics_tracks_dead_code_allow_attributes(self) -> None:
        text = (
            "#![allow(dead_code)]\n"
            "#[allow(clippy::too_many_lines)]\n"
            "#[allow(dead_code, reason = \"staged\")]\n"
        )
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["allow_attrs"], 3)
        self.assertEqual(metrics["dead_code_allow_attrs"], 2)
