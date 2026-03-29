"""Tests for shared Python function scanning helpers."""

from __future__ import annotations

import unittest

from dev.scripts.checks.code_shape_function_policy import scan_python_functions


class ScanPythonFunctionsTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
