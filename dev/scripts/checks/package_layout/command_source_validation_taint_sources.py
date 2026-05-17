"""Source-detection helpers for command-source taint classification."""

from __future__ import annotations

import ast

try:
    from .command_source_validation_taint_imports import SUBPROCESS_METHODS
except ImportError:  # pragma: no cover
    from command_source_validation_taint_imports import SUBPROCESS_METHODS

CLI_CONTAINER_NAMES = frozenset({"args", "namespace", "options", "opts", "parsed_args"})
CONFIG_CONTAINER_NAMES = frozenset({"cfg", "config", "payload", "settings"})
VALIDATOR_TOKENS = ("allowlist", "sanitize", "trusted", "validate", "validated")


def is_validator_call(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Name):
        name = node.func.id
    elif isinstance(node.func, ast.Attribute):
        name = node.func.attr
    else:
        name = ""
    lowered = name.lower()
    return any(token in lowered for token in VALIDATOR_TOKENS)


def is_shlex_split_call(node: ast.Call, imports: dict[str, set[str]]) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "split":
        return isinstance(func.value, ast.Name) and func.value.id in imports["shlex_modules"]
    return isinstance(func, ast.Name) and func.id in imports["shlex_split_names"]


def is_environ_attribute(expr: ast.expr, imports: dict[str, set[str]]) -> bool:
    return (
        isinstance(expr, ast.Attribute)
        and expr.attr == "environ"
        and isinstance(expr.value, ast.Name)
        and expr.value.id in imports["os_modules"]
    )


def is_env_source(expr: ast.expr, imports: dict[str, set[str]]) -> bool:
    if isinstance(expr, ast.Call):
        return _is_env_call(expr, imports)
    if isinstance(expr, ast.Subscript):
        if is_environ_attribute(expr.value, imports):
            return True
        return isinstance(expr.value, ast.Name) and expr.value.id in imports["environ_names"]
    return False


def _is_env_call(expr: ast.Call, imports: dict[str, set[str]]) -> bool:
    func = expr.func
    if isinstance(func, ast.Name):
        return func.id in imports["getenv_names"]
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr == "getenv":
        return isinstance(func.value, ast.Name) and func.value.id in imports["os_modules"]
    if func.attr != "get":
        return False
    if is_environ_attribute(func.value, imports):
        return True
    return isinstance(func.value, ast.Name) and func.value.id in imports["environ_names"]


def is_sys_argv_source(expr: ast.expr, imports: dict[str, set[str]]) -> bool:
    if isinstance(expr, ast.Name):
        return expr.id in imports["argv_names"]
    if isinstance(expr, ast.Attribute):
        return (
            expr.attr == "argv"
            and isinstance(expr.value, ast.Name)
            and expr.value.id in imports["sys_modules"]
        )
    if isinstance(expr, ast.Subscript):
        return is_sys_argv_source(expr.value, imports)
    return False
