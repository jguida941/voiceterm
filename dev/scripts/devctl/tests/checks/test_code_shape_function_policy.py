"""Tests for shared Python function scanning helpers."""

from __future__ import annotations

import subprocess
import sys
import unittest

from dev.scripts.devctl.config import REPO_ROOT
from dev.scripts.checks.code_shape.code_shape_function_policy import (
    scan_python_functions,
)


class ScanPythonFunctionsTests(unittest.TestCase):
    def test_root_shim_import_stays_loadable_from_checks_root(self) -> None:
        script = "\n".join(
            [
                "import sys",
                f"sys.path.insert(0, {str((REPO_ROOT / 'dev/scripts/checks')).__repr__()})",
                "import code_shape_function_policy",
                "assert hasattr(code_shape_function_policy, 'scan_rust_functions')",
                "assert hasattr(code_shape_function_policy, 'scan_python_functions')",
            ]
        )

        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_multiline_signature_excludes_signature_continuations_from_body(self) -> None:
        code = "\n".join(
            [
                "def sample(",
                "    first,",
                "    second,",
                ") -> None:",
                '    marker = "body"',
                "    return None",
            ]
        )

        functions = scan_python_functions(code)

        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]["start_line"], 1)
        self.assertEqual(functions[0]["end_line"], 6)
        self.assertEqual(functions[0]["line_count"], 6)

    def test_multiline_signature_with_comments_still_finds_real_body_end(self) -> None:
        code = "\n".join(
            [
                "def other(",
                "    first,",
                "    second,",
                ") -> None:",
                "    # body comment",
                "    value = first + second",
                "",
                "    return value",
                "",
                "outside = True",
            ]
        )

        functions = scan_python_functions(code)

        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]["name"], "other")
        self.assertEqual(functions[0]["end_line"], 8)

    def test_inline_comment_after_signature_colon_does_not_crash(self) -> None:
        code = "\n".join(
            [
                "def main() -> None:  # pragma: no cover - thin wrapper",
                '    marker = "#"',
                "    return None",
            ]
        )

        functions = scan_python_functions(code)

        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]["name"], "main")
        self.assertEqual(functions[0]["end_line"], 3)

    def test_default_string_hash_in_signature_is_not_treated_as_comment(self) -> None:
        code = "\n".join(
            [
                'def render(marker: str = "#") -> str:  # pragma: no cover',
                "    return marker",
            ]
        )

        functions = scan_python_functions(code)

        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]["name"], "render")
        self.assertEqual(functions[0]["line_count"], 2)

    def test_indented_method_signature_with_annotations_is_detected(self) -> None:
        code = "\n".join(
            [
                "class Runner:",
                "    def __init__(",
                "        self,",
                "        spec: str,",
                "        python_executable: str | None = None,",
                "    ) -> None:",
                "        self.spec = spec",
                "",
                "    def run(self) -> None:",
                "        return None",
            ]
        )

        functions = scan_python_functions(code)

        self.assertEqual([function["name"] for function in functions], ["__init__", "run"])
        self.assertEqual(functions[0]["end_line"], 7)
        self.assertEqual(functions[1]["end_line"], 10)


if __name__ == "__main__":
    unittest.main()
