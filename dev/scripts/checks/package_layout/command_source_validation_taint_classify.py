"""Expression-classification helpers for command-source taint detection."""

from __future__ import annotations

import ast

try:
    from .command_source_validation_taint_sources import (
        CLI_CONTAINER_NAMES,
        CONFIG_CONTAINER_NAMES,
        is_env_source,
        is_shlex_split_call,
        is_sys_argv_source,
        is_validator_call,
    )
except ImportError:  # pragma: no cover
    from command_source_validation_taint_sources import (
        CLI_CONTAINER_NAMES,
        CONFIG_CONTAINER_NAMES,
        is_env_source,
        is_shlex_split_call,
        is_sys_argv_source,
        is_validator_call,
    )


def iter_child_expressions(expr: ast.AST) -> list[ast.expr]:
    return [child for child in ast.iter_child_nodes(expr) if isinstance(child, ast.expr)]


def classify_expression(
    expr: ast.expr | None,
    *,
    bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
) -> set[str]:
    if expr is None:
        return set()
    if is_env_source(expr, imports):
        return {"env"}
    if is_sys_argv_source(expr, imports):
        return {"argv"}
    if isinstance(expr, ast.Name):
        return set(bindings.get(expr.id, set()))
    if isinstance(expr, ast.Attribute):
        return _classify_attribute(expr, bindings=bindings, imports=imports)
    if isinstance(expr, ast.Subscript):
        return _classify_subscript(expr, bindings=bindings, imports=imports)
    if isinstance(expr, ast.Starred):
        return classify_expression(expr.value, bindings=bindings, imports=imports)
    if isinstance(expr, ast.Call):
        return _classify_call(expr, bindings=bindings, imports=imports)
    return _classify_child_expressions(expr, bindings=bindings, imports=imports)


def _classify_attribute(
    expr: ast.Attribute,
    *,
    bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
) -> set[str]:
    if isinstance(expr.value, ast.Name):
        if expr.value.id in CLI_CONTAINER_NAMES:
            return {"cli"}
        if expr.value.id in CONFIG_CONTAINER_NAMES:
            return {"config"}
    return classify_expression(expr.value, bindings=bindings, imports=imports)


def _classify_subscript(
    expr: ast.Subscript,
    *,
    bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
) -> set[str]:
    if isinstance(expr.value, ast.Name) and expr.value.id in CONFIG_CONTAINER_NAMES:
        return {"config"}
    return classify_expression(expr.value, bindings=bindings, imports=imports)


def _classify_call(
    expr: ast.Call,
    *,
    bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
) -> set[str]:
    if is_validator_call(expr):
        return set()
    if not is_shlex_split_call(expr, imports):
        return _classify_child_expressions(expr, bindings=bindings, imports=imports)
    nested = classify_expression(
        expr.args[0] if expr.args else None,
        bindings=bindings,
        imports=imports,
    )
    if nested & {"argv", "cli", "config", "env", "split"}:
        return {"split"}
    return set()


def _classify_child_expressions(
    expr: ast.AST,
    *,
    bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
) -> set[str]:
    taints: set[str] = set()
    for child in iter_child_expressions(expr):
        taints.update(classify_expression(child, bindings=bindings, imports=imports))
    return taints


def extract_assigned_names(target: ast.expr) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if not isinstance(target, (ast.Tuple, ast.List)):
        return []
    names: list[str] = []
    for element in target.elts:
        names.extend(extract_assigned_names(element))
    return names


def bind_assignment_targets(
    bindings: dict[str, set[str]],
    target: ast.expr,
    taints: set[str],
) -> None:
    for name in extract_assigned_names(target):
        bindings[name] = set(taints)
