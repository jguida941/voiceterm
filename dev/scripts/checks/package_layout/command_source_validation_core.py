"""AST analysis for Python command-source validation."""

from __future__ import annotations

import ast
if __package__:
    from .command_source_validation_taint import (
        SUBPROCESS_METHODS,
        bind_assignment_targets,
        classify_expression,
        collect_import_bindings,
        is_shlex_split_call,
    )
else:  # pragma: no cover - standalone script fallback
    from command_source_validation_taint import (
        SUBPROCESS_METHODS,
        bind_assignment_targets,
        classify_expression,
        collect_import_bindings,
        is_shlex_split_call,
    )

TRY_LIKE_STATEMENTS = (ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)
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


def _extract_command_expr(node: ast.Call) -> ast.expr | None:
    if node.args:
        return node.args[0]
    for keyword in node.keywords:
        if keyword.arg in {"args", "argv", "cmd"}:
            return keyword.value
    return None


def _shell_enabled(node: ast.Call) -> bool:
    for keyword in node.keywords:
        if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
            return True
    return False


def _append_violation(
    violations: list[dict[str, object]],
    seen: set[tuple[int, str]],
    *,
    line: int,
    reason: str,
) -> None:
    key = (line, reason)
    if key in seen:
        return
    seen.add(key)
    violations.append({"line": line, "reason": reason})


def _scan_statement_calls(
    statement: ast.stmt,
    *,
    bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
    wrapper_names: set[str],
    violations: list[dict[str, object]],
    seen: set[tuple[int, str]],
) -> None:
    for node in ast.walk(statement):
        if not isinstance(node, ast.Call):
            continue
        if is_shlex_split_call(node, imports):
            _scan_shlex_split(node, bindings=bindings, imports=imports, violations=violations, seen=seen)
        if _call_uses_command_runner(node, imports=imports, wrapper_names=wrapper_names):
            _scan_command_runner(node, bindings=bindings, imports=imports, violations=violations, seen=seen)


def _scan_shlex_split(
    node: ast.Call,
    *,
    bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
    violations: list[dict[str, object]],
    seen: set[tuple[int, str]],
) -> None:
    taints = classify_expression(
        node.args[0] if node.args else None,
        bindings=bindings,
        imports=imports,
    )
    if taints & {"argv", "cli", "config", "env", "split"}:
        _append_violation(
            violations,
            seen,
            line=node.lineno,
            reason="shlex.split() on CLI/env/config input requires structured args or validation",
        )


def _scan_command_runner(
    node: ast.Call,
    *,
    bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
    violations: list[dict[str, object]],
    seen: set[tuple[int, str]],
) -> None:
    if _shell_enabled(node):
        _append_violation(
            violations,
            seen,
            line=node.lineno,
            reason="command execution enables shell=True",
        )
    taints = classify_expression(
        _extract_command_expr(node),
        bindings=bindings,
        imports=imports,
    )
    if "argv" in taints:
        _append_violation(
            violations,
            seen,
            line=node.lineno,
            reason="command argv forwards sys.argv without validation",
        )
    if "env" in taints:
        _append_violation(
            violations,
            seen,
            line=node.lineno,
            reason="command argv uses env-controlled values without validation",
        )


def _merge_bindings(*binding_maps: dict[str, set[str]]) -> dict[str, set[str]]:
    merged: dict[str, set[str]] = {}
    for mapping in binding_maps:
        for name, taints in mapping.items():
            merged.setdefault(name, set()).update(taints)
    return merged


def _apply_assignment_bindings(
    bindings: dict[str, set[str]],
    statement: ast.Assign | ast.AnnAssign,
    *,
    imports: dict[str, set[str]],
) -> None:
    value = statement.value if isinstance(statement, ast.Assign) else statement.value
    taints = classify_expression(value, bindings=bindings, imports=imports)
    targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
    for target in targets:
        bind_assignment_targets(bindings, target, taints)


def _analyze_branch(
    statements: list[ast.stmt],
    *,
    bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
    wrapper_names: set[str],
    violations: list[dict[str, object]],
    seen: set[tuple[int, str]],
) -> dict[str, set[str]]:
    return _analyze_statements(
        statements,
        initial_bindings=bindings,
        imports=imports,
        wrapper_names=wrapper_names,
        violations=violations,
        seen=seen,
    )


def _merge_try_like_bindings(
    statement: ast.stmt,
    *,
    bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
    wrapper_names: set[str],
    violations: list[dict[str, object]],
    seen: set[tuple[int, str]],
) -> dict[str, set[str]]:
    merged = _merge_bindings(
        bindings,
        _analyze_branch(
            statement.body,
            bindings=bindings,
            imports=imports,
            wrapper_names=wrapper_names,
            violations=violations,
            seen=seen,
        ),
        _analyze_branch(
            getattr(statement, "orelse", []),
            bindings=bindings,
            imports=imports,
            wrapper_names=wrapper_names,
            violations=violations,
            seen=seen,
        ),
    )
    for handler in getattr(statement, "handlers", []):
        merged = _merge_bindings(
            merged,
            _analyze_branch(
                handler.body,
                bindings=merged,
                imports=imports,
                wrapper_names=wrapper_names,
                violations=violations,
                seen=seen,
            ),
        )
    if isinstance(statement, ast.Try):
        merged = _merge_bindings(
            merged,
            _analyze_branch(
                statement.finalbody,
                bindings=merged,
                imports=imports,
                wrapper_names=wrapper_names,
                violations=violations,
                seen=seen,
            ),
        )
    return merged


def _analyze_statements(
    statements: list[ast.stmt],
    *,
    initial_bindings: dict[str, set[str]],
    imports: dict[str, set[str]],
    wrapper_names: set[str],
    violations: list[dict[str, object]],
    seen: set[tuple[int, str]],
) -> dict[str, set[str]]:
    bindings = {name: set(taints) for name, taints in initial_bindings.items()}
    for statement in statements:
        _scan_statement_calls(
            statement,
            bindings=bindings,
            imports=imports,
            wrapper_names=wrapper_names,
            violations=violations,
            seen=seen,
        )
        if isinstance(statement, FUNCTION_STATEMENTS):
            _analyze_branch(
                statement.body,
                bindings={},
                imports=imports,
                wrapper_names=wrapper_names,
                violations=violations,
                seen=seen,
            )
            continue
        if isinstance(statement, ast.Assign):
            _apply_assignment_bindings(bindings, statement, imports=imports)
            continue
        if isinstance(statement, ast.AnnAssign) and statement.value is not None:
            _apply_assignment_bindings(bindings, statement, imports=imports)
            continue
        if isinstance(statement, ast.If):
            bindings = _merge_bindings(
                bindings,
                _analyze_branch(
                    statement.body,
                    bindings=bindings,
                    imports=imports,
                    wrapper_names=wrapper_names,
                    violations=violations,
                    seen=seen,
                ),
                _analyze_branch(
                    statement.orelse,
                    bindings=bindings,
                    imports=imports,
                    wrapper_names=wrapper_names,
                    violations=violations,
                    seen=seen,
                ),
            )
            continue
        if isinstance(statement, TRY_LIKE_STATEMENTS):
            bindings = _merge_try_like_bindings(
                statement,
                bindings=bindings,
                imports=imports,
                wrapper_names=wrapper_names,
                violations=violations,
                seen=seen,
            )
    return bindings


def analyze_python_text(text: str) -> tuple[int, list[dict[str, object]]]:
    tree = ast.parse(text)
    imports = collect_import_bindings(tree)
    wrapper_names = _collect_command_wrapper_names(tree, imports)
    violations: list[dict[str, object]] = []
    seen: set[tuple[int, str]] = set()
    _analyze_statements(
        tree.body,
        initial_bindings={},
        imports=imports,
        wrapper_names=wrapper_names,
        violations=violations,
        seen=seen,
    )
    command_call_count = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _call_uses_command_runner(node, imports=imports, wrapper_names=wrapper_names)
    )
    sorted_violations = sorted(
        violations,
        key=lambda item: (int(item["line"]), str(item["reason"])),
    )
    return command_call_count, sorted_violations
