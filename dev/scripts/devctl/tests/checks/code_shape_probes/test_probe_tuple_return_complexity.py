"""Tests for the tuple-return complexity review probe."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[6]
SCRIPT_PATH = (
    REPO_ROOT
    / "dev/scripts/checks/code_shape_probes/probe_tuple_return_complexity.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "probe_tuple_return_complexity_script",
        SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load probe_tuple_return_complexity.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_module()


class TupleReturnComplexityProbeTests(unittest.TestCase):
    def test_counts_top_level_tuple_elements(self) -> None:
        self.assertEqual(mod._count_top_level_tuple_elements("(bool, bool, bool)"), 3)
        self.assertEqual(
            mod._count_top_level_tuple_elements("(Result<String, Error>, usize, bool)"),
            3,
        )
        self.assertEqual(mod._count_top_level_tuple_elements("String"), 0)

    def test_extract_return_type_skips_result_wrapped_tuple(self) -> None:
        sig = "fn parse() -> Result<(bool, bool, bool), Error> {"
        self.assertIsNone(mod._extract_return_type(sig))

    def test_scan_rust_file_flags_bare_three_tuple_return(self) -> None:
        rust_text = """
fn dispatch() -> (bool, bool, bool) {
    let redraw = true;
    let should_exit = false;
    let flushed = true;
    (redraw, should_exit, flushed)
}
""".strip()

        hints = mod._scan_rust_file(rust_text, Path("rust/src/sample.rs"))

        self.assertEqual(len(hints), 1)
        hint = hints[0]
        self.assertEqual(hint.symbol, "dispatch")
        self.assertEqual(hint.severity, "medium")
        self.assertEqual(hint.risk_type, "design_smell")
        self.assertIn("3-element tuple", hint.signals[0])

    def test_scan_rust_file_ignores_result_wrapped_tuple(self) -> None:
        rust_text = """
fn parse() -> Result<(bool, bool, bool), ParseError> {
    Ok((true, false, true))
}
""".strip()

        hints = mod._scan_rust_file(rust_text, Path("rust/src/sample.rs"))

        self.assertEqual(hints, [])

    def test_scan_rust_file_flags_four_tuple_as_high(self) -> None:
        rust_text = """
fn dispatch() -> (bool, bool, bool, bool) {
    (true, false, true, false)
}
""".strip()

        hints = mod._scan_rust_file(rust_text, Path("rust/src/sample.rs"))

        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].severity, "high")


if __name__ == "__main__":
    unittest.main()
