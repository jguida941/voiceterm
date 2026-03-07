"""Unit tests for runtime panic policy guard parsing behavior."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT

SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_rust_runtime_panic_policy.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(
        "check_rust_runtime_panic_policy_script",
        SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_rust_runtime_panic_policy.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckRustRuntimePanicPolicyTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def test_find_unallowlisted_panic_lines_skips_allowlisted_comment(self) -> None:
        text = (
            "fn demo() {\n"
            "    // panic-policy: allow reason=static invariant guard\n"
            '    panic!("allowed");\n'
            '    panic!("not allowed");\n'
            "}\n"
        )
        line_numbers = self.script._find_unallowlisted_panic_lines(text)
        self.assertEqual(line_numbers, [4])

    def test_allow_marker_without_reason_does_not_allow(self) -> None:
        text = (
            "fn demo() {\n"
            "    // panic-policy: allow\n"
            '    panic!("still unallowlisted");\n'
            "}\n"
        )
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["unallowlisted_panic_calls"], 1)
        self.assertEqual(metrics["unallowlisted_panic_line_numbers"], [3])

    def test_count_metrics_ignores_cfg_test_blocks(self) -> None:
        text = (
            "fn runtime() {\n"
            '    panic!("runtime");\n'
            "}\n"
            "#[cfg(test)]\n"
            "mod tests {\n"
            "    fn helper() {\n"
            '        panic!("test only");\n'
            "    }\n"
            "}\n"
        )
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["unallowlisted_panic_calls"], 1)
        self.assertEqual(metrics["unallowlisted_panic_line_numbers"], [2])

    def test_count_metrics_counts_multiple_panic_macros_on_same_line(self) -> None:
        text = "fn runtime() {\n" '    panic!("left"); panic!("right");\n' "}\n"
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["unallowlisted_panic_calls"], 2)
        self.assertEqual(metrics["unallowlisted_panic_line_numbers"], [2, 2])

    def test_count_metrics_ignores_panic_text_inside_strings_and_comments(self) -> None:
        text = (
            "fn runtime() {\n"
            '    let _message = "panic!(\\"string\\")";\n'
            '    // panic!("comment")\n'
            '    panic!("real");\n'
            "}\n"
        )
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["unallowlisted_panic_calls"], 1)
        self.assertEqual(metrics["unallowlisted_panic_line_numbers"], [4])

    def test_count_metrics_ignores_cfg_any_test_blocks(self) -> None:
        text = (
            "fn runtime() {\n"
            '    panic!("runtime");\n'
            "}\n"
            '#[cfg(any(test, feature = "bench"))]\n'
            "mod tests {\n"
            "    fn helper() {\n"
            '        panic!("test only");\n'
            "    }\n"
            "}\n"
        )
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["unallowlisted_panic_calls"], 1)
        self.assertEqual(metrics["unallowlisted_panic_line_numbers"], [2])

    def test_count_metrics_keeps_cfg_not_test_runtime_blocks(self) -> None:
        text = (
            "fn runtime() {\n"
            '    panic!("runtime");\n'
            "}\n"
            "#[cfg(not(test))]\n"
            "fn runtime_only_helper() {\n"
            '    panic!("also runtime");\n'
            "}\n"
        )
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["unallowlisted_panic_calls"], 2)
        self.assertEqual(metrics["unallowlisted_panic_line_numbers"], [2, 6])
