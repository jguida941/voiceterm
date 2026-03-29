"""Tests for the design-smells review probe."""

from __future__ import annotations

from pathlib import Path
import unittest

from dev.scripts.devctl.tests.conftest import load_repo_module

SCRIPT = load_repo_module(
    "probe_design_smells_script",
    "dev/scripts/checks/probe_design_smells.py",
)


class ProbeDesignSmellsTests(unittest.TestCase):
    def test_scan_function_smells_flags_first_multiline_object_param(self) -> None:
        source = "\n".join(
            [
                "def choose(",
                "    payload: object,",
                ") -> str:",
                "    name = getattr(payload, 'name')",
                "    kind = getattr(payload, 'kind')",
                "    return f'{name}:{kind}'",
            ]
        )

        hints = SCRIPT._scan_function_smells(
            source,
            Path("dev/scripts/devctl/runtime/sample.py"),
        )

        self.assertEqual(len(hints), 1)
        self.assertIn(
            "parameter 'payload: object' accessed via getattr() 2 times",
            hints[0].signals[0],
        )

    def test_scan_function_smells_flags_first_single_line_object_param(self) -> None:
        source = "\n".join(
            [
                "def choose(payload: object) -> str:",
                "    name = getattr(payload, 'name')",
                "    kind = getattr(payload, 'kind')",
                "    return f'{name}:{kind}'",
            ]
        )

        hints = SCRIPT._scan_function_smells(
            source,
            Path("dev/scripts/devctl/runtime/sample.py"),
        )

        self.assertEqual(len(hints), 1)
        self.assertIn(
            "parameter 'payload: object' accessed via getattr() 2 times",
            hints[0].signals[0],
        )


if __name__ == "__main__":
    unittest.main()
