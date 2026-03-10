"""Tests for check_facade_wrappers guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "checks" / "check_facade_wrappers.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("check_facade_wrappers", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


class TestIsPureDelegation:
    def test_return_call(self):
        import ast
        code = "def foo(x):\n    return bar(x)\n"
        tree = ast.parse(code)
        func = tree.body[0]
        assert mod._is_pure_delegation(func) is True

    def test_expr_call(self):
        import ast
        code = "def foo(x):\n    bar(x)\n"
        tree = ast.parse(code)
        func = tree.body[0]
        assert mod._is_pure_delegation(func) is True

    def test_multi_statement_not_delegation(self):
        import ast
        code = "def foo(x):\n    y = x + 1\n    return bar(y)\n"
        tree = ast.parse(code)
        func = tree.body[0]
        assert mod._is_pure_delegation(func) is False

    def test_return_non_call(self):
        import ast
        code = "def foo(x):\n    return x + 1\n"
        tree = ast.parse(code)
        func = tree.body[0]
        assert mod._is_pure_delegation(func) is False


class TestCountFacadeWrappers:
    def test_none_returns_zero(self):
        assert mod._count_facade_wrappers(None) == 0

    def test_syntax_error_returns_zero(self):
        assert mod._count_facade_wrappers("def broken(") == 0

    def test_no_wrappers(self):
        code = "def foo(x):\n    y = x + 1\n    return y\n"
        assert mod._count_facade_wrappers(code) == 0

    def test_single_wrapper(self):
        code = "def foo(x):\n    return bar(x)\n"
        assert mod._count_facade_wrappers(code) == 1

    def test_multiple_wrappers(self):
        code = "\n".join([
            "def a(): return real_a()",
            "def b(): return real_b()",
            "def c(): return real_c()",
            "def d(): return real_d()",
        ])
        assert mod._count_facade_wrappers(code) == 4


class TestIsFacadeHeavy:
    def test_below_threshold(self):
        code = "\n".join([
            "def a(): return real_a()",
            "def b(): return real_b()",
            "def c(): return real_c()",
        ])
        assert mod._is_facade_heavy(code) is False

    def test_at_threshold(self):
        code = "\n".join([
            "def a(): return real_a()",
            "def b(): return real_b()",
            "def c(): return real_c()",
        ])
        assert mod._is_facade_heavy(code) is False

    def test_above_threshold(self):
        code = "\n".join([
            "def a(): return real_a()",
            "def b(): return real_b()",
            "def c(): return real_c()",
            "def d(): return real_d()",
        ])
        assert mod._is_facade_heavy(code) is True

    def test_none(self):
        assert mod._is_facade_heavy(None) is False


class TestCountMetrics:
    def test_clean_file(self):
        result = mod._count_metrics("x = 1")
        assert result == {"facade_heavy_modules": 0, "facade_wrappers": 0}

    def test_facade_heavy_file(self):
        code = "\n".join([
            "def a(): return real_a()",
            "def b(): return real_b()",
            "def c(): return real_c()",
            "def d(): return real_d()",
        ])
        result = mod._count_metrics(code)
        assert result["facade_heavy_modules"] == 1
        assert result["facade_wrappers"] == 4


class TestGrowth:
    def test_positive_growth(self):
        base = {"facade_heavy_modules": 0, "facade_wrappers": 2}
        current = {"facade_heavy_modules": 1, "facade_wrappers": 5}
        growth = mod._growth(base, current)
        assert mod._has_positive_growth(growth)

    def test_no_growth(self):
        base = {"facade_heavy_modules": 1, "facade_wrappers": 4}
        current = {"facade_heavy_modules": 1, "facade_wrappers": 4}
        growth = mod._growth(base, current)
        assert not mod._has_positive_growth(growth)

    def test_only_wrapper_growth_not_flagged(self):
        """Growth is only flagged when facade_heavy_modules increases."""
        base = {"facade_heavy_modules": 0, "facade_wrappers": 1}
        current = {"facade_heavy_modules": 0, "facade_wrappers": 3}
        growth = mod._growth(base, current)
        assert not mod._has_positive_growth(growth)


class TestRenderMd:
    def test_clean_report(self):
        report = {
            "mode": "working-tree",
            "ok": True,
            "files_changed": 5,
            "files_considered": 3,
            "files_skipped_non_python": 1,
            "files_skipped_tests": 1,
            "violations": [],
            "since_ref": None,
            "head_ref": None,
            "totals": {
                "facade_heavy_modules_growth": 0,
                "facade_wrappers_growth": 0,
            },
        }
        md = mod._render_md(report)
        assert "# check_facade_wrappers" in md
        assert "ok: True" in md
