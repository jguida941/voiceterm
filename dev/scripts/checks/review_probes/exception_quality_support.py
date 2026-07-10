"""Shared AST helpers for the exception-quality review probe."""

from __future__ import annotations

import ast


def handler_kind(node_type: ast.expr | None) -> str | None:
    if node_type is None:
        return "bare"
    if isinstance(node_type, ast.Tuple):
        return tuple_handler_kind(node_type)
    if isinstance(node_type, ast.Name):
        name = node_type.id
    elif isinstance(node_type, ast.Attribute):
        name = node_type.attr
    else:
        return None
    if name in {"Exception", "BaseException"}:
        return name
    return None


def tuple_handler_kind(node_type: ast.Tuple) -> str | None:
    members: set[str] = set()
    for element in node_type.elts:
        kind = handler_kind(element)
        if kind is not None:
            members.add(kind)
    if not members:
        return None
    return ",".join(sorted(members))


def name_set(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


def call_context_names(call: ast.Call) -> set[str]:
    names: set[str] = set()
    for arg in call.args:
        names.update(name_set(arg))
    for keyword in call.keywords:
        if keyword.value is not None:
            names.update(name_set(keyword.value))
    return names


def is_generic_raise_message(node: ast.Raise, exc_name: str | None) -> bool:
    if node.exc is None:
        return False
    if not isinstance(node.exc, ast.Call):
        return False
    if not node.exc.args:
        return True
    if node.cause is None:
        return False
    if not isinstance(node.cause, ast.Name):
        return False
    if exc_name is None or node.cause.id != exc_name:
        return False
    first_arg = node.exc.args[0]
    context_names = call_context_names(node.exc)
    allowed = {exc_name}
    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
        return not context_names or context_names <= allowed
    if isinstance(first_arg, ast.JoinedStr):
        return not context_names or context_names <= allowed
    return False


def iter_generic_translation_raises(
    node: ast.ExceptHandler,
    exc_name: str | None,
) -> list[ast.Raise]:
    matches: list[ast.Raise] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and is_generic_raise_message(child, exc_name):
            matches.append(child)
    return matches
