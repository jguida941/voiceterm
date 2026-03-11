"""Shared AST helpers for Python default-state trap guards."""

from __future__ import annotations

import ast

MUTABLE_DEFAULT_FACTORIES = frozenset({"list", "dict", "set", "defaultdict", "deque"})
METRIC_LABELS = {
    "global_statements": "global_statements",
    "mutable_default_args": "mutable_default_args",
    "function_call_default_args": "function_call_default_args",
    "dataclass_mutable_defaults": "dataclass_mutable_defaults",
    "dataclass_call_defaults": "dataclass_call_defaults",
}


def _parse_tree(text: str | None) -> ast.AST | None:
    if text is None:
        return None
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def count_global_statements(text: str | None) -> int:
    tree = _parse_tree(text)
    if tree is None:
        return 0
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            count += len(node.names)
    return count


def _default_is_mutable(node: ast.AST) -> bool:
    if isinstance(node, (ast.List, ast.Dict, ast.Set)):
        return True
    if isinstance(node, ast.Call):
        target = node.func
        if isinstance(target, ast.Name):
            return target.id in MUTABLE_DEFAULT_FACTORIES
        if isinstance(target, ast.Attribute):
            return target.attr in MUTABLE_DEFAULT_FACTORIES
    return False


def _iter_function_defaults(tree: ast.AST) -> tuple[ast.AST, ...]:
    defaults: list[ast.AST] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        defaults.extend(node.args.defaults)
        defaults.extend(item for item in node.args.kw_defaults if item is not None)
    return tuple(defaults)


def count_mutable_default_args(text: str | None) -> int:
    tree = _parse_tree(text)
    if tree is None:
        return 0
    return sum(1 for default in _iter_function_defaults(tree) if _default_is_mutable(default))


def count_function_call_default_args(text: str | None) -> int:
    tree = _parse_tree(text)
    if tree is None:
        return 0
    return sum(
        1
        for default in _iter_function_defaults(tree)
        if isinstance(default, ast.Call) and not _default_is_mutable(default)
    )


def _is_dataclass_decorator(node: ast.AST) -> bool:
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Name):
        return target.id == "dataclass"
    if isinstance(target, ast.Attribute):
        return target.attr == "dataclass"
    return False


def _is_field_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id == "field"
    if isinstance(node.func, ast.Attribute):
        return node.func.attr == "field"
    return False


def _is_classvar_annotation(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "ClassVar"
    if isinstance(node, ast.Attribute):
        return node.attr == "ClassVar"
    if isinstance(node, ast.Subscript):
        return _is_classvar_annotation(node.value)
    return False


def _classify_dataclass_default(node: ast.AST) -> str | None:
    if _is_field_call(node):
        assert isinstance(node, ast.Call)
        keyword_map = {
            keyword.arg: keyword.value
            for keyword in node.keywords
            if keyword.arg is not None
        }
        if "default_factory" in keyword_map:
            default_factory = keyword_map["default_factory"]
            if isinstance(default_factory, ast.Call):
                return "call"
            return None
        default_value = keyword_map.get("default")
        if default_value is None:
            return None
        if _default_is_mutable(default_value):
            return "mutable"
        if isinstance(default_value, ast.Call):
            return "call"
        return None
    if _default_is_mutable(node):
        return "mutable"
    if isinstance(node, ast.Call):
        return "call"
    return None


def count_dataclass_default_traps(text: str | None) -> dict[str, int]:
    tree = _parse_tree(text)
    counts = {
        "dataclass_mutable_defaults": 0,
        "dataclass_call_defaults": 0,
    }
    if tree is None:
        return counts
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(_is_dataclass_decorator(decorator) for decorator in node.decorator_list):
            continue
        for statement in node.body:
            if not isinstance(statement, ast.AnnAssign):
                continue
            if statement.value is None:
                continue
            if _is_classvar_annotation(statement.annotation):
                continue
            category = _classify_dataclass_default(statement.value)
            if category == "mutable":
                counts["dataclass_mutable_defaults"] += 1
            elif category == "call":
                counts["dataclass_call_defaults"] += 1
    return counts


def count_metrics(text: str | None) -> dict[str, int]:
    metrics = {
        "global_statements": count_global_statements(text),
        "mutable_default_args": count_mutable_default_args(text),
        "function_call_default_args": count_function_call_default_args(text),
    }
    metrics.update(count_dataclass_default_traps(text))
    return metrics


def format_growth(growth: dict[str, int]) -> str:
    parts = [
        f"{METRIC_LABELS[key]} {value:+d}"
        for key, value in growth.items()
        if value != 0
    ]
    return ", ".join(parts) if parts else "none"
