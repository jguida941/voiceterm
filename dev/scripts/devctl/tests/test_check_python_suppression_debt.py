"""Tests for check_python_suppression_debt guard."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.tests.conftest import (
    init_python_guard_repo_root,
    load_repo_module,
)

SCRIPT = load_repo_module(
    "check_python_suppression_debt",
    "dev/scripts/checks/check_python_suppression_debt.py",
)


class CheckPythonSuppressionDebtTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_python_guard_repo_root(self)

    def _write(self, relative_path: str, text: str) -> str:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return relative_path

    def test_count_suppressions_tracks_supported_directives(self) -> None:
        counts = SCRIPT._count_suppressions(
            "\n".join(
                (
                    "from typing import Any  # noqa: F401",
                    "value = cast(Any, item)  # type: ignore[arg-type]",
                    "# pylint: disable=too-many-return-statements",
                    "# pyright: ignore[reportAssignmentType]",
                )
            )
        )

        self.assertEqual(
            counts,
            {
                "noqa": 1,
                "type_ignore": 1,
                "pylint_disable": 1,
                "pyright_ignore": 1,
            },
        )

    def test_count_suppressions_ignores_string_literals(self) -> None:
        counts = SCRIPT._count_suppressions('EXAMPLE = "# noqa: F401"\n')
        self.assertEqual(counts, SCRIPT._empty_counts())

    def test_report_flags_positive_growth(self) -> None:
        relative_path = self._write(
            "dev/scripts/example.py",
            "from typing import Any  # noqa: F401\nvalue = cast(Any, item)  # type: ignore[arg-type]\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[self.root / relative_path],
            base_text_by_path={relative_path: ""},
            current_text_by_path={relative_path: (self.root / relative_path).read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"],
            [
                {
                    "path": relative_path,
                    "base": SCRIPT._empty_counts(),
                    "current": {
                        "noqa": 1,
                        "type_ignore": 1,
                        "pylint_disable": 0,
                        "pyright_ignore": 0,
                    },
                    "growth": {
                        "noqa": 1,
                        "type_ignore": 1,
                        "pylint_disable": 0,
                        "pyright_ignore": 0,
                    },
                }
            ],
        )

    def test_report_allows_equal_or_lower_suppression_count(self) -> None:
        relative_path = self._write(
            "app/operator_console/example.py",
            "from typing import Any\nvalue = cast(Any, item)\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[self.root / relative_path],
            base_text_by_path={relative_path: "from typing import Any  # noqa: F401\n"},
            current_text_by_path={relative_path: (self.root / relative_path).read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["totals"]["noqa_growth"], -1)

    def test_report_ignores_paths_outside_configured_roots(self) -> None:
        relative_path = self._write(
            "scripts/example.py",
            "from typing import Any  # noqa: F401\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[self.root / relative_path],
            base_text_by_path={relative_path: ""},
            current_text_by_path={relative_path: (self.root / relative_path).read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["files_considered"], 0)
        self.assertEqual(report["files_skipped_non_python"], 1)


if __name__ == "__main__":
    unittest.main()
