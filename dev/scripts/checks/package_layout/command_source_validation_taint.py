"""Taint classification helpers for command-source validation."""

from __future__ import annotations

import ast

CLI_CONTAINER_NAMES = frozenset({"args", "namespace", "options", "opts", "parsed_args"})
CONFIG_CONTAINER_NAMES = frozenset({"cfg", "config", "payload", "settings"})
VALIDATOR_TOKENS = ("allowlist", "sanitize", "trusted", "validate", "validated")
SUBPROCESS_METHODS = frozenset({"Popen", "call", "check_call", "check_output", "run"})


def collect_import_bindings(tree: ast.AST) -> dict[str, set[str]]:
    bindings = {
        "os_modules": {"os"},
        "sys_modules": {"sys"},
        "shlex_modules": {"shlex"},
        "subprocess_modules": {"subprocess"},
        "argv_names": set(),
        "environ_names": set(),
        "getenv_names": set(),
        "shlex_split_names": set(),
        "subprocess_func_names": set(),
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os":
                    bindings["os_modules"].add(alias.asname or alias.name)
                elif alias.name == "sys":
                    bindings["sys_modules"].add(alias.asname or alias.name)
                elif alias.name == "shlex":
                    bindings["shlex_modules"].add(alias.asname or alias.name)
                elif alias.name == "subprocess":
                    bindings["subprocess_modules"].add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            _collect_import_from_bindings(bindings, node)
    return bindings


def _collect_import_from_bindings(bindings: dict[str, set[str]], node: ast.ImportFrom) -> None:
    if node.module == "os":
        for alias in node.names:
            if alias.name == "environ":
                bindings["environ_names"].add(alias.asname or alias.name)
            elif alias.name == "getenv":
                bindings["getenv_names"].add(alias.asname or alias.name)
        return
    if node.module == "sys":
        for alias in node.names:
            if alias.name == "argv":
                bindings["argv_names"].add(alias.asname or alias.name)
        return
    if node.module == "shlex":
        for alias in node.names:
            if alias.name == "split":
                bindings["shlex_split_names"].add(alias.asname or alias.name)
        return
    if node.module == "subprocess":
        for alias in node.names:
            if alias.name in SUBPROCESS_METHODS:
                bindings["subprocess_func_names"].add(alias.asname or alias.name)


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
