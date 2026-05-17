"""Unit tests for the AST-backed field-route reference helper.

These tests exercise ``_file_references_any`` in isolation against synthetic
source files created under ``tmp_path``. They lock the behavior that a
field-route proof requires an *executable* reference (identifier, attribute,
dotted chain, or string-literal key) and that docstring mentions do not count.

The regression for the F1 finding against the real ``dashboard_render``
package lives alongside the full contract-closure tests in
``test_check_platform_contract_closure.py``; this file covers the helper
contract that those route checks depend on.
"""

from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.platform_contract_closure.field_routes_surface_state import (
    _dotted_attribute,
    _file_references_any,
)


def _write_module(path: Path, body: str) -> Path:
    """Create a Python file at *path* with *body* and return the path."""
    path.write_text(body, encoding="utf-8")
    return path


def test_matches_attribute_access(tmp_path: Path) -> None:
    """``obj.top_blocker`` counts as an executable reference."""
    source = _write_module(
        tmp_path / "attr.py",
        "def render(model):\n    return model.top_blocker\n",
    )
    assert _file_references_any(source, ("top_blocker",)) is True


def test_matches_bare_identifier(tmp_path: Path) -> None:
    """A bare ``top_blocker`` identifier counts as an executable reference."""
    source = _write_module(
        tmp_path / "name.py",
        "top_blocker = 'x'\n",
    )
    assert _file_references_any(source, ("top_blocker",)) is True


def test_matches_string_literal_dict_key(tmp_path: Path) -> None:
    """``d.get('top_blocker', ...)`` counts as an executable reference."""
    source = _write_module(
        tmp_path / "dict_key.py",
        "def render(snapshot):\n"
        "    return snapshot.get('top_blocker', 'none')\n",
    )
    assert _file_references_any(source, ("top_blocker",)) is True


def test_matches_dotted_attribute_chain(tmp_path: Path) -> None:
    """A dotted-form token such as ``auto_state.phase`` matches its AST path."""
    source = _write_module(
        tmp_path / "dotted.py",
        "def build(auto_state):\n    return auto_state.phase\n",
    )
    assert _file_references_any(source, ("auto_state.phase",)) is True


def test_ignores_module_docstring(tmp_path: Path) -> None:
    """A token appearing only in a module docstring must NOT count."""
    source = _write_module(
        tmp_path / "module_doc.py",
        '"""This module documents top_blocker but does not use it."""\n'
        "def render(snapshot):\n    return snapshot\n",
    )
    assert _file_references_any(source, ("top_blocker",)) is False


def test_ignores_function_docstring(tmp_path: Path) -> None:
    """A token appearing only in a function docstring must NOT count."""
    source = _write_module(
        tmp_path / "func_doc.py",
        "def render(snapshot):\n"
        '    """Renders top_blocker from the snapshot."""\n'
        "    return snapshot\n",
    )
    assert _file_references_any(source, ("top_blocker",)) is False


def test_ignores_class_docstring(tmp_path: Path) -> None:
    """A token appearing only in a class docstring must NOT count."""
    source = _write_module(
        tmp_path / "class_doc.py",
        "class Renderer:\n"
        '    """This class handles top_blocker rendering elsewhere."""\n'
        "    def render(self, snapshot):\n        return snapshot\n",
    )
    assert _file_references_any(source, ("top_blocker",)) is False


def test_distinguishes_similar_prefixed_tokens(tmp_path: Path) -> None:
    """Exact-match semantics: ``push_eligible_now`` must not match ``push_eligible``.

    The previous raw-text ``in`` match conflated these two attribute names via
    substring. The AST walk enforces exact equality on identifier, attribute,
    and string-literal nodes so distinct fields stay distinct.
    """
    source = _write_module(
        tmp_path / "prefixed.py",
        "def render(receipt):\n    return receipt.get('push_eligible_now')\n",
    )
    assert _file_references_any(source, ("push_eligible",)) is False
    assert _file_references_any(source, ("push_eligible_now",)) is True


def test_returns_false_for_unparseable_source(tmp_path: Path) -> None:
    """A file that cannot be parsed as Python returns False, not an exception.

    Fail-closed default: an unparseable consumer cannot prove field-route
    closure, so the caller must treat it as missing rather than falling back
    to raw-text matching (the behavior the F1 fix was written to remove).
    """
    source = _write_module(tmp_path / "broken.py", "def broken(:\n")
    assert _file_references_any(source, ("top_blocker",)) is False


def test_dotted_attribute_resolves_name_root() -> None:
    """``_dotted_attribute`` reconstructs an ``a.b`` chain rooted at a Name."""
    import ast

    tree = ast.parse("x.y.z")
    expr = tree.body[0]
    assert isinstance(expr, ast.Expr)
    assert isinstance(expr.value, ast.Attribute)
    assert _dotted_attribute(expr.value) == "x.y.z"


def test_dotted_attribute_returns_none_for_non_name_root() -> None:
    """Chains whose root is not a bare ``Name`` return ``None``.

    The helper is conservative: it refuses to synthesize a dotted path when
    the root is a call, subscript, or other non-name expression, so callers
    fall back to the shallower ``node.attr`` match instead of treating
    arbitrary expressions as dotted field references.
    """
    import ast

    tree = ast.parse("f().y.z")
    expr = tree.body[0]
    assert isinstance(expr, ast.Expr)
    assert isinstance(expr.value, ast.Attribute)
    assert _dotted_attribute(expr.value) is None
