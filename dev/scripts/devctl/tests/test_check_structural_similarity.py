"""Tests for check_structural_similarity guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "checks" / "check_structural_similarity.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("check_structural_similarity", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


class TestNormalizePythonBody:
    def test_replaces_identifiers(self):
        code = "def foo():\n" + "\n".join(f"    x{i} = {i}" for i in range(10))
        funcs = mod.scan_python_functions(code)
        result = mod._normalize_python_body(code, funcs[0])
        assert result is not None
        assert "foo" not in result
        assert "x0" not in result

    def test_short_body_returns_none(self):
        code = "def foo():\n    return 1\n"
        funcs = mod.scan_python_functions(code)
        result = mod._normalize_python_body(code, funcs[0])
        assert result is None

    def test_replaces_strings_and_numbers(self):
        lines = ["def bar():"]
        for i in range(10):
            lines.append(f'    msg{i} = "hello {i}"')
        code = "\n".join(lines)
        funcs = mod.scan_python_functions(code)
        result = mod._normalize_python_body(code, funcs[0])
        assert result is not None
        assert '"hello' not in result


class TestStructuralHash:
    def test_deterministic(self):
        body = "_ = _\n_ = _\n_ = _"
        h1 = mod._structural_hash(body)
        h2 = mod._structural_hash(body)
        assert h1 == h2

    def test_different_inputs_differ(self):
        h1 = mod._structural_hash("_ = _\n_ = _")
        h2 = mod._structural_hash("_ = _\nif _:\n    _ = _")
        assert h1 != h2


class TestCollectFingerprints:
    def test_none_returns_empty(self):
        assert mod._collect_fingerprints(None, suffix=".py", path_str="x.py") == []

    def test_unknown_suffix_returns_empty(self):
        assert mod._collect_fingerprints("x = 1", suffix=".txt", path_str="x.txt") == []

    def test_python_fingerprints(self):
        lines = ["def process():"]
        for i in range(10):
            lines.append(f"    step_{i} = compute({i})")
        code = "\n".join(lines)
        result = mod._collect_fingerprints(code, suffix=".py", path_str="a.py")
        assert len(result) == 1
        assert result[0]["name"] == "process"
        assert result[0]["path"] == "a.py"
        assert "hash" in result[0]


class TestCountCrossFileSimilarPairs:
    def test_no_cross_file(self):
        fps = [
            {"path": "a.py", "name": "f", "hash": "abc", "lines": 10},
            {"path": "a.py", "name": "g", "hash": "abc", "lines": 10},
        ]
        assert mod._count_cross_file_similar_pairs(fps) == 0

    def test_cross_file_pair(self):
        fps = [
            {"path": "a.py", "name": "f", "hash": "abc", "lines": 10},
            {"path": "b.py", "name": "g", "hash": "abc", "lines": 10},
        ]
        assert mod._count_cross_file_similar_pairs(fps) == 1

    def test_three_files_same_hash(self):
        fps = [
            {"path": "a.py", "name": "f", "hash": "abc", "lines": 10},
            {"path": "b.py", "name": "g", "hash": "abc", "lines": 10},
            {"path": "c.py", "name": "h", "hash": "abc", "lines": 10},
        ]
        assert mod._count_cross_file_similar_pairs(fps) == 2

    def test_different_hashes_no_pairs(self):
        fps = [
            {"path": "a.py", "name": "f", "hash": "aaa", "lines": 10},
            {"path": "b.py", "name": "g", "hash": "bbb", "lines": 10},
        ]
        assert mod._count_cross_file_similar_pairs(fps) == 0


class TestGrowth:
    def test_positive_growth(self):
        base = {"structural_similar_pairs": 0}
        current = {"structural_similar_pairs": 2}
        growth = mod._growth(base, current)
        assert mod._has_positive_growth(growth)

    def test_no_growth(self):
        base = {"structural_similar_pairs": 3}
        current = {"structural_similar_pairs": 3}
        growth = mod._growth(base, current)
        assert not mod._has_positive_growth(growth)

    def test_negative_growth(self):
        base = {"structural_similar_pairs": 5}
        current = {"structural_similar_pairs": 2}
        growth = mod._growth(base, current)
        assert not mod._has_positive_growth(growth)
