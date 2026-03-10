"""Tests for check_parameter_count guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "checks" / "check_parameter_count.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_parameter_count", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


class TestCountRustHighParamFns:
    def test_no_functions(self):
        assert mod._count_rust_high_param_fns("struct Foo;") == 0

    def test_below_threshold(self):
        code = "fn foo(a: i32, b: i32, c: i32) -> i32 { a + b + c }"
        assert mod._count_rust_high_param_fns(code) == 0

    def test_above_threshold(self):
        params = ", ".join(f"p{i}: i32" for i in range(9))
        code = f"fn many({params}) -> i32 {{ 0 }}"
        assert mod._count_rust_high_param_fns(code) == 1

    def test_self_excluded(self):
        params = ", ".join(f"p{i}: i32" for i in range(7))
        code = f"fn method(&self, {params}) -> i32 {{ 0 }}"
        assert mod._count_rust_high_param_fns(code) == 0

    def test_none_input(self):
        assert mod._count_rust_high_param_fns(None) == 0


class TestCountPythonHighParamFns:
    def test_no_functions(self):
        assert mod._count_python_high_param_fns("x = 1") == 0

    def test_below_threshold(self):
        code = "def foo(a, b, c, d):\n    pass"
        assert mod._count_python_high_param_fns(code) == 0

    def test_above_threshold(self):
        params = ", ".join(f"p{i}" for i in range(8))
        code = f"def many({params}):\n    pass"
        assert mod._count_python_high_param_fns(code) == 1

    def test_self_excluded(self):
        params = ", ".join(f"p{i}" for i in range(6))
        code = f"class C:\n    def method(self, {params}):\n        pass"
        assert mod._count_python_high_param_fns(code) == 0

    def test_none_input(self):
        assert mod._count_python_high_param_fns(None) == 0

    def test_syntax_error_returns_zero(self):
        assert mod._count_python_high_param_fns("def broken(") == 0


class TestCountMetrics:
    def test_rust(self):
        result = mod._count_metrics("fn foo() {}", suffix=".rs")
        assert result == {"high_param_functions": 0}

    def test_python(self):
        result = mod._count_metrics("x = 1", suffix=".py")
        assert result == {"high_param_functions": 0}

    def test_unknown_suffix(self):
        result = mod._count_metrics("whatever", suffix=".txt")
        assert result == {"high_param_functions": 0}


class TestGrowth:
    def test_no_growth(self):
        base = {"high_param_functions": 1}
        current = {"high_param_functions": 1}
        assert mod._growth(base, current) == {"high_param_functions": 0}

    def test_positive_growth(self):
        base = {"high_param_functions": 0}
        current = {"high_param_functions": 2}
        growth = mod._growth(base, current)
        assert mod._has_positive_growth(growth)

    def test_negative_growth(self):
        base = {"high_param_functions": 3}
        current = {"high_param_functions": 1}
        growth = mod._growth(base, current)
        assert not mod._has_positive_growth(growth)
