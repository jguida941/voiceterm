"""Statement-scan helpers for command-source validation."""

from __future__ import annotations

import ast

try:
    from .command_source_validation_core_runner import _call_uses_command_runner
    from .command_source_validation_taint import classify_expression, is_shlex_split_call
except ImportError:  # pragma: no cover
    from command_source_validation_core_runner import _call_uses_command_runner
    from command_source_validation_taint import classify_expression, is_shlex_split_call


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
