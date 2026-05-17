"""Command-runner detection helpers for command-source validation."""

from __future__ import annotations

import ast

try:
    from .command_source_validation_taint import SUBPROCESS_METHODS
except ImportError:  # pragma: no cover
    from command_source_validation_taint import SUBPROCESS_METHODS

FUNCTION_STATEMENTS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _call_uses_subprocess_sink(node: ast.Call, imports: dict[str, set[str]]) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in SUBPROCESS_METHODS:
        return isinstance(func.value, ast.Name) and func.value.id in imports["subprocess_modules"]
    return isinstance(func, ast.Name) and func.id in imports["subprocess_func_names"]


def _collect_command_wrapper_names(tree: ast.Module, imports: dict[str, set[str]]) -> set[str]:
    wrappers: set[str] = set()
    for node in tree.body:
        if not isinstance(node, FUNCTION_STATEMENTS):
            continue
        if any(
            isinstance(child, ast.Call) and _call_uses_subprocess_sink(child, imports)
            for child in ast.walk(node)
        ):
            wrappers.add(node.name)
    return wrappers


def _call_uses_command_runner(
    node: ast.Call,
    *,
    imports: dict[str, set[str]],
    wrapper_names: set[str],
) -> bool:
    return _call_uses_subprocess_sink(node, imports) or (
        isinstance(node.func, ast.Name) and node.func.id in wrapper_names
    )
