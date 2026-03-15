"""Tests for check_python_design_complexity guard."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import (
    init_python_guard_repo_root,
    load_repo_module,
)

SCRIPT = load_repo_module(
    "check_python_design_complexity",
    "dev/scripts/checks/check_python_design_complexity.py",
)


class CheckPythonDesignComplexityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_python_guard_repo_root(self)

    def _write(self, relative_path: str, text: str) -> str:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return relative_path

    def test_function_metrics_include_class_methods(self) -> None:
        metrics = SCRIPT._collect_excessive_functions(
            "class Sample:\n"
            "    def render(self):\n"
            "        if flag:\n"
            "            return 1\n"
            "        return 0\n",
            thresholds={"max_branches": 0, "max_returns": 0},
        )

        self.assertIn("Sample.render", metrics)
        self.assertEqual(metrics["Sample.render"]["branches"], 1)
        self.assertEqual(metrics["Sample.render"]["returns"], 2)

    def test_report_flags_new_branch_and_return_heavy_function(self) -> None:
        relative_path = self._write(
            "dev/scripts/example.py",
            "def build_report(flag_a, flag_b, flag_c):\n"
            "    if flag_a:\n"
            "        return 1\n"
            "    if flag_b:\n"
            "        return 2\n"
            "    if flag_c:\n"
            "        return 3\n"
            "    return 4\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[self.root / relative_path],
            base_text_by_path={relative_path: ""},
            current_text_by_path={relative_path: (self.root / relative_path).read_text(encoding="utf-8")},
            mode="working-tree",
            guard_config={"max_branches": 2, "max_returns": 2},
        )

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"][0]["growth"],
            {
                "high_branch_functions": 1,
                "high_return_functions": 1,
            },
        )

    def test_report_flags_growth_for_existing_over_budget_function(self) -> None:
        relative_path = self._write(
            "app/operator_console/example.py",
            "def run(flag_a, flag_b, flag_c, flag_d):\n"
            "    if flag_a:\n"
            "        return 1\n"
            "    if flag_b:\n"
            "        return 2\n"
            "    if flag_c:\n"
            "        return 3\n"
            "    if flag_d:\n"
            "        return 4\n"
            "    return 5\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[Path(relative_path)],
            base_text_by_path={
                relative_path: (
                    "def run(flag_a, flag_b, flag_c):\n"
                    "    if flag_a:\n"
                    "        return 1\n"
                    "    if flag_b:\n"
                    "        return 2\n"
                    "    if flag_c:\n"
                    "        return 3\n"
                    "    return 4\n"
                )
            },
            current_text_by_path={relative_path: (self.root / relative_path).read_text(encoding="utf-8")},
            mode="working-tree",
            guard_config={"max_branches": 2, "max_returns": 10},
        )

        self.assertFalse(report["ok"])
        function_row = report["violations"][0]["functions"][0]
        self.assertIn("too_many_branches", function_row["reasons"])
        self.assertNotIn("too_many_returns", function_row["reasons"])

    def test_report_skips_python_tests(self) -> None:
        relative_path = self._write(
            "dev/scripts/tests/test_example.py",
            "def build(flag):\n    return flag\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[Path(relative_path)],
            base_text_by_path={relative_path: ""},
            current_text_by_path={relative_path: "def build(flag):\n    return flag\n"},
            mode="working-tree",
            guard_config={"max_branches": 1, "max_returns": 1},
        )

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["files_considered"], 0)
        self.assertEqual(report["files_skipped_tests"], 1)


if __name__ == "__main__":
    unittest.main()
