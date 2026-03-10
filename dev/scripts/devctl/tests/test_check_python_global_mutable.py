"""Tests for check_python_global_mutable guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "checks" / "check_python_global_mutable.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("check_python_global_mutable", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


class TestCountGlobalStatements:
    def test_no_globals(self):
        assert mod._count_global_statements("x = 1\ndef foo():\n    pass") == 0

    def test_single_global(self):
        code = "x = None\ndef foo():\n    global x\n    x = 1"
        assert mod._count_global_statements(code) == 1

    def test_multi_name_global(self):
        code = "x = None\ny = None\ndef foo():\n    global x, y\n    x = 1"
        assert mod._count_global_statements(code) == 2

    def test_multiple_global_statements(self):
        code = (
            "a = None\nb = None\n"
            "def foo():\n    global a\n    a = 1\n"
            "def bar():\n    global b\n    b = 2\n"
        )
        assert mod._count_global_statements(code) == 2

    def test_none_input(self):
        assert mod._count_global_statements(None) == 0

    def test_syntax_error(self):
        assert mod._count_global_statements("def broken(") == 0


class TestCountMetrics:
    def test_basic(self):
        code = "x = None\ndef foo():\n    global x\n    x = 1"
        result = mod._count_metrics(code)
        assert result == {"global_statements": 1, "mutable_default_args": 0}


class TestMutableDefaultArgs:
    def test_no_mutable_defaults(self):
        code = "def sample(flag: bool = False):\n    return flag\n"
        assert mod._count_mutable_default_args(code) == 0

    def test_literal_mutable_defaults(self):
        code = (
            "def sample(items=[]):\n    return items\n"
            "def other(mapping={}):\n    return mapping\n"
        )
        assert mod._count_mutable_default_args(code) == 2

    def test_factory_mutable_defaults(self):
        code = (
            "def sample(items=list()):\n    return items\n"
            "def other(values=set()):\n    return values\n"
        )
        assert mod._count_mutable_default_args(code) == 2

    def test_none_input(self):
        assert mod._count_mutable_default_args(None) == 0

    def test_syntax_error(self):
        assert mod._count_mutable_default_args("def broken(") == 0


class TestGrowth:
    def test_no_growth(self):
        base = {"global_statements": 1, "mutable_default_args": 0}
        current = {"global_statements": 1, "mutable_default_args": 0}
        assert not mod._has_positive_growth(mod._growth(base, current))

    def test_positive_growth(self):
        base = {"global_statements": 0, "mutable_default_args": 0}
        current = {"global_statements": 0, "mutable_default_args": 1}
        assert mod._has_positive_growth(mod._growth(base, current))
