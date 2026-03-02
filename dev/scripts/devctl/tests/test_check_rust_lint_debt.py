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
        self.assertEqual(metrics["unwrap_expect_calls"], 1)

    def test_count_metrics_handles_none_input(self) -> None:
        metrics = self.script._count_metrics(None)
        self.assertEqual(metrics["allow_attrs"], 0)
        self.assertEqual(metrics["unwrap_expect_calls"], 0)
