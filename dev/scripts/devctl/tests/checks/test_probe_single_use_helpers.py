"""Tests for cross-file continuity in `probe_single_use_helpers`."""

from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from dev.scripts.devctl.tests.conftest import load_repo_module

mod = load_repo_module(
    "probe_single_use_helpers",
    "dev/scripts/checks/probe_single_use_helpers.py",
)


class ProbeSingleUseHelpersTests(TestCase):
    def test_cross_file_call_counts_still_flag_moved_helper(self) -> None:
        current = {
            Path("pkg/origin.py"): (
                "from .support import _moved_helper\n\n"
                "def run() -> None:\n"
                "    _moved_helper()\n"
            ),
            Path("pkg/support.py"): (
                "def _moved_helper() -> None:\n"
                "    first = 1\n"
                "    second = first + 1\n"
                "    third = second + 1\n"
                "    print(third)\n"
            ),
        }

        single_use = mod._single_use_helpers_by_file(current)

        self.assertEqual(
            [candidate.name for candidate in single_use[Path("pkg/support.py")]],
            ["_moved_helper"],
        )

    def test_relocation_hint_triggers_below_regular_threshold(self) -> None:
        current = {
            Path("pkg/origin.py"): (
                "from .support import _moved_helper\n\n"
                "def run() -> None:\n"
                "    _moved_helper()\n"
            ),
            Path("pkg/support.py"): (
                "def _moved_helper() -> None:\n"
                "    first = 1\n"
                "    second = first + 1\n"
                "    third = second + 1\n"
                "    print(third)\n"
            ),
        }
        base = {
            Path("pkg/origin.py"): (
                "def _moved_helper() -> None:\n"
                "    first = 1\n"
                "    second = first + 1\n"
                "    third = second + 1\n"
                "    print(third)\n\n"
                "def run() -> None:\n"
                "    _moved_helper()\n"
            ),
        }

        hints = mod._scan_python_files(
            current,
            base_text_by_path=base,
            base_path_by_current_path={
                Path("pkg/origin.py"): Path("pkg/origin.py"),
                Path("pkg/support.py"): Path("pkg/support.py"),
            },
        )

        support_hint = next(
            hint for hint in hints if hint.file == "pkg/support.py"
        )
        self.assertEqual(support_hint.severity, "high")
        self.assertIn("single-use helper relocation detected", support_hint.signals[0] + " " + " ".join(support_hint.signals[1:]))
        self.assertIn("moved", support_hint.ai_instruction)
