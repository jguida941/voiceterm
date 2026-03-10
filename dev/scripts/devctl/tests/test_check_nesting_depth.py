"""Tests for check_nesting_depth guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "checks" / "check_nesting_depth.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_nesting_depth", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


class TestMaxPythonNesting:
    def test_shallow(self):
        code = "def foo():\n    x = 1\n    return x\n"
        assert mod._max_python_nesting(code) == 0

    def test_deeply_nested(self):
        code = (
            "def deep():\n"
            "    if True:\n"
            "        for x in y:\n"
            "            if x:\n"
            "                for z in w:\n"
            "                    if z:\n"
            "                        pass\n"
        )
        assert mod._max_python_nesting(code) == 1

    def test_at_threshold(self):
        code = (
            "def border():\n"
            "    if True:\n"
            "        for x in y:\n"
            "            if x:\n"
            "                for z in w:\n"
            "                    pass\n"
        )
        assert mod._max_python_nesting(code) == 0

    def test_none_input(self):
        assert mod._max_python_nesting(None) == 0

    def test_no_functions(self):
        assert mod._max_python_nesting("x = 1") == 0


class TestScanPythonFunctionDepth:
    def test_basic(self):
        lines = [
            "def foo():",
            "    if True:",
            "        pass",
            "",
        ]
        depth, next_i = mod._scan_python_function_depth(lines, 1, 0)
        assert depth == 1


class TestMaxRustNesting:
    def test_shallow(self):
        code = "fn foo() {\n    let x = 1;\n}\n"
        assert mod._max_rust_nesting(code) == 0

    def test_none_input(self):
        assert mod._max_rust_nesting(None) == 0


class TestCountMetrics:
    def test_python(self):
        code = "def foo():\n    pass\n"
        result = mod._count_metrics(code, suffix=".py")
        assert result == {"deeply_nested_functions": 0}

    def test_rust(self):
        code = "fn foo() {\n    let x = 1;\n}\n"
        result = mod._count_metrics(code, suffix=".rs")
        assert result == {"deeply_nested_functions": 0}

    def test_unknown(self):
        result = mod._count_metrics("whatever", suffix=".txt")
        assert result == {"deeply_nested_functions": 0}


class TestGrowth:
    def test_positive(self):
        base = {"deeply_nested_functions": 0}
        current = {"deeply_nested_functions": 1}
        assert mod._has_positive_growth(mod._growth(base, current))

    def test_no_growth(self):
        base = {"deeply_nested_functions": 1}
        current = {"deeply_nested_functions": 1}
        assert not mod._has_positive_growth(mod._growth(base, current))
