"""Tests for check_python_dict_schema guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "checks" / "check_python_dict_schema.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("check_python_dict_schema", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


class TestCountLargeDictLiterals:
    def test_small_dict(self):
        code = 'x = {"a": 1, "b": 2}'
        assert mod._count_large_dict_literals(code) == 0

    def test_large_dict(self):
        keys = ", ".join(f'"{chr(97 + i)}": {i}' for i in range(7))
        code = f"x = {{{keys}}}"
        assert mod._count_large_dict_literals(code) == 1

    def test_non_string_keys(self):
        keys = ", ".join(f"{i}: {i}" for i in range(10))
        code = f"x = {{{keys}}}"
        assert mod._count_large_dict_literals(code) == 0

    def test_none_input(self):
        assert mod._count_large_dict_literals(None) == 0

    def test_syntax_error(self):
        assert mod._count_large_dict_literals("x = {broken") == 0

    def test_nested_dicts_counted_separately(self):
        inner_keys = ", ".join(f'"{chr(97 + i)}": {i}' for i in range(7))
        outer_keys = ", ".join(f'"{chr(65 + i)}": {i}' for i in range(7))
        code = f"x = {{{outer_keys}, \"inner\": {{{inner_keys}}}}}"
        assert mod._count_large_dict_literals(code) == 2


class TestCountMetrics:
    def test_basic(self):
        result = mod._count_metrics("x = 1")
        assert result == {"large_dict_literals": 0, "weak_dict_any_aliases": 0}


class TestWeakDictAnyAliases:
    def test_argument_def_alias(self):
        code = "ArgumentDef = dict[str, Any]"
        assert mod._count_weak_dict_any_aliases(code) == 1

    def test_nested_dict_any_alias(self):
        code = "ArgumentDefs = list[dict[str, Any]]"
        assert mod._count_weak_dict_any_aliases(code) == 1

    def test_non_alias_lowercase_target_ignored(self):
        code = "argument_def = dict[str, Any]"
        assert mod._count_weak_dict_any_aliases(code) == 0

    def test_non_any_dict_alias_ignored(self):
        code = "ArgumentDef = dict[str, str]"
        assert mod._count_weak_dict_any_aliases(code) == 0


class TestGrowth:
    def test_positive(self):
        base = {"large_dict_literals": 0, "weak_dict_any_aliases": 0}
        current = {"large_dict_literals": 1, "weak_dict_any_aliases": 0}
        assert mod._has_positive_growth(mod._growth(base, current))

    def test_no_growth(self):
        base = {"large_dict_literals": 2, "weak_dict_any_aliases": 1}
        current = {"large_dict_literals": 2, "weak_dict_any_aliases": 1}
        assert not mod._has_positive_growth(mod._growth(base, current))
