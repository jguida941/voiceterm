"""Tests for check_python_broad_except guard script."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import init_temp_repo_root, load_repo_module

SCRIPT = load_repo_module(
    "check_python_broad_except",
    "dev/scripts/checks/check_python_broad_except.py",
)


class CheckPythonBroadExceptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_temp_repo_root(
            self, "dev/scripts", "app/operator_console"
        )

    def _write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_report_flags_new_broad_exception_without_rationale(self) -> None:
        path = self._write(
            "dev/scripts/example.py",
            (
                "def sample() -> None:\n"
                "    try:\n"
                "        run()\n"
                "    except Exception as exc:\n"
                "        print(exc)\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            added_lines_by_path={"dev/scripts/example.py": {4}},
            mode="working-tree",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"],
            [
                {
                    "path": "dev/scripts/example.py",
                    "line": 4,
                    "kind": "Exception",
                    "reason": (
                        "new broad exception handler is missing "
                        "`broad-except: allow reason=...` rationale"
                    ),
                }
            ],
        )

    def test_report_accepts_rationale_comment_above_handler(self) -> None:
        path = self._write(
            "app/operator_console/example.py",
            (
                "def sample() -> None:\n"
                "    try:\n"
                "        run()\n"
                "    # broad-except: allow reason=UI refresh should fail soft.\n"
                "    except BaseException as exc:\n"
                "        print(exc)\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            added_lines_by_path={"app/operator_console/example.py": {5}},
            mode="working-tree",
        )

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["documented_candidate_handlers"], 1)

    def test_report_ignores_existing_broad_exception_when_handler_line_not_added(
        self,
    ) -> None:
        path = self._write(
            "dev/scripts/stable.py",
            (
                "def sample() -> None:\n"
                "    try:\n"
                "        run()\n"
                "    except Exception as exc:\n"
                "        print(exc)\n"
                "    return None\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            added_lines_by_path={"dev/scripts/stable.py": {6}},
            mode="working-tree",
        )

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["candidate_handlers"], 0)

    def test_report_flags_tuple_handler_when_exception_is_in_tuple(self) -> None:
        path = self._write(
            "dev/scripts/tuple_case.py",
            (
                "def sample() -> None:\n"
                "    try:\n"
                "        run()\n"
                "    except (RuntimeError, Exception) as exc:\n"
                "        print(exc)\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            added_lines_by_path={"dev/scripts/tuple_case.py": {4}},
            mode="working-tree",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["violations"][0]["kind"], "Exception")

    def test_report_ignores_test_files(self) -> None:
        path = self._write(
            "dev/scripts/devctl/tests/test_policy.py",
            (
                "def sample() -> None:\n"
                "    try:\n"
                "        run()\n"
                "    except Exception:\n"
                "        pass\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            added_lines_by_path={"dev/scripts/devctl/tests/test_policy.py": None},
            mode="paths",
        )

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["files_scanned"], 0)
        self.assertEqual(report["files_skipped_tests"], 1)


if __name__ == "__main__":
    unittest.main()
