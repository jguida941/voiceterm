"""Surface-state field-route closure proofs for platform contract enforcement.

Each check verifies that a key field from a surface-state contract
(ControlPlaneReadModel, AutoModeState, SessionCachePacket) is consumed
in the declared target surface renderer by inspecting the actual
source code for field-access references.

Field-route proof must reflect *executable* consumption: identifier or
attribute access, dotted attribute chains, or string-literal keys used
in code. References that appear only in module, class, or function
docstrings (or in comments) are excluded, because a docstring mention
does not prove that the renderer actually reads the field at runtime.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _source_contains_any(module_path: str, tokens: tuple[str, ...]) -> bool:
    """Return True when non-docstring code at *module_path* references any token.

    Resolves dotted module paths to filesystem paths relative to the
    repo root. Accepts both flat modules (``foo/bar.py``) and packages
    (``foo/bar/__init__.py``); for packages, scans every ``*.py`` file
    in the package root so tokens rendered by submodules still count.
    Executable match is required: a token that appears only in a module,
    class, or function docstring does not satisfy the field-route proof.
    """
    rel_module = module_path.replace(".", "/")
    flat_path = _REPO_ROOT / f"{rel_module}.py"
    if flat_path.is_file():
        return _file_references_any(flat_path, tokens)

    package_dir = _REPO_ROOT / rel_module
    if package_dir.is_dir():
        for py_file in sorted(package_dir.glob("*.py")):
            if _file_references_any(py_file, tokens):
                return True
    return False


def _file_references_any(path: Path, tokens: tuple[str, ...]) -> bool:
    """Return True if *path* has an executable (non-docstring) reference to any token.

    Parses the file as Python AST, strips module/class/function docstrings,
    and walks the remaining tree looking for:

    - ``ast.Name`` nodes whose ``id`` matches a token (bare identifier use),
    - ``ast.Attribute`` nodes whose ``attr`` matches a token (``obj.field``),
    - ``ast.Attribute`` nodes whose reconstructed dotted chain matches a
      dotted token (``auto_state.phase``),
    - ``ast.Constant`` string values equal to a token (``d["field"]`` /
      ``d.get("field", ...)``).

    Returns False if the file cannot be parsed as valid Python. This is a
    fail-closed default: an unparseable consumer cannot prove field-route
    closure, and the caller should treat it as a missing reference rather
    than falling back to raw-text scanning.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return False

    _strip_docstrings(tree)
    token_set = set(tokens)

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id in token_set:
                return True
        elif isinstance(node, ast.Attribute):
            if node.attr in token_set:
                return True
            dotted = _dotted_attribute(node)
            if dotted is not None and dotted in token_set:
                return True
        elif isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, str) and value in token_set:
                return True
    return False


def _strip_docstrings(tree: ast.AST) -> None:
    """Drop module/class/function docstrings from *tree* in-place.

    A docstring is the first statement of a module, class, or function body
    when that statement is an ``ast.Expr`` wrapping a string ``ast.Constant``.
    Removing it before the reference walk means a field name that appears
    only in documentation does not count as executable consumption.
    """
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body.pop(0)


def _dotted_attribute(node: ast.Attribute) -> str | None:
    """Reconstruct a dotted attribute chain such as ``a.b.c`` from nested nodes.

    Returns the dotted string when the chain terminates in an ``ast.Name``
    (for example ``auto_state.phase`` for ``Attribute(attr='phase',
    value=Name('auto_state'))``). Returns ``None`` for subscripts, calls, or
    any non-name root so the caller falls back to the shallower ``node.attr``
    match rather than treating arbitrary expressions as dotted paths.
    """
    parts: list[str] = [node.attr]
    current: ast.AST = node.value
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def _build_coverage(
    contract_id: str,
    field_name: str,
    route_id: str,
    consumer: str,
) -> dict[str, object]:
    return {
        "kind": "field_route",
        "contract_id": contract_id,
        "field_name": field_name,
        "route_id": route_id,
        "consumer": consumer,
        "ok": True,
    }


def _build_violation(
    coverage: dict[str, object],
    detail: str,
) -> dict[str, object]:
    return {
        "kind": "field_route",
        "contract_id": coverage["contract_id"],
        "field_name": coverage["field_name"],
        "route_id": coverage["route_id"],
        "rule": "unconsumed-field-route",
        "detail": detail,
    }
