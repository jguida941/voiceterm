"""Tests for check_god_class guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "checks" / "check_god_class.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_god_class", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


class TestCountPythonGodClasses:
    def test_small_class(self):
        code = "class Foo:\n    def a(self): pass\n    def b(self): pass\n"
        assert mod._count_python_god_classes(code) == 0

    def test_many_methods(self):
        methods = "\n".join(f"    def m{i}(self): pass" for i in range(22))
        code = f"class God:\n{methods}\n"
        assert mod._count_python_god_classes(code) == 1

    def test_many_ivars(self):
        ivars = "\n".join(f"        self.v{i} = None" for i in range(12))
        code = f"class Wide:\n    def __init__(self):\n{ivars}\n"
        assert mod._count_python_god_classes(code) == 1

    def test_below_both_thresholds(self):
        methods = "\n".join(f"    def m{i}(self): pass" for i in range(18))
        ivars = "\n".join(f"        self.v{i} = None" for i in range(8))
        code = f"class Ok:\n    def __init__(self):\n{ivars}\n{methods}\n"
        assert mod._count_python_god_classes(code) == 0

    def test_none_input(self):
        assert mod._count_python_god_classes(None) == 0

    def test_syntax_error(self):
        assert mod._count_python_god_classes("class broken(") == 0


class TestCountRustGodImpls:
    def test_small_impl(self):
        code = "impl Foo {\n    fn a(&self) {}\n    fn b(&self) {}\n}\n"
        assert mod._count_rust_god_impls(code) == 0

    def test_many_methods(self):
        methods = "\n".join(f"    fn m{i}(&self) {{}}" for i in range(22))
        code = f"impl God {{\n{methods}\n}}\n"
        assert mod._count_rust_god_impls(code) == 1

    def test_split_impls_combined(self):
        methods_a = "\n".join(f"    fn a{i}(&self) {{}}" for i in range(12))
        methods_b = "\n".join(f"    fn b{i}(&self) {{}}" for i in range(12))
        code = f"impl Split {{\n{methods_a}\n}}\nimpl Split {{\n{methods_b}\n}}\n"
        assert mod._count_rust_god_impls(code) == 1

    def test_none_input(self):
        assert mod._count_rust_god_impls(None) == 0


class TestCountMetrics:
    def test_python(self):
        result = mod._count_metrics("class Foo:\n    pass\n", suffix=".py")
        assert result == {"god_classes": 0}

    def test_rust(self):
        result = mod._count_metrics("impl Foo {\n    fn a(&self) {}\n}\n", suffix=".rs")
        assert result == {"god_classes": 0}

    def test_unknown(self):
        result = mod._count_metrics("whatever", suffix=".txt")
        assert result == {"god_classes": 0}


class TestGrowth:
    def test_positive(self):
        base = {"god_classes": 0}
        current = {"god_classes": 1}
        assert mod._has_positive_growth(mod._growth(base, current))

    def test_no_growth(self):
        base = {"god_classes": 1}
        current = {"god_classes": 1}
        assert not mod._has_positive_growth(mod._growth(base, current))
