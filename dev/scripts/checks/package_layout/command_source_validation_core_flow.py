"""Control-flow helpers for command-source validation."""

from __future__ import annotations

import ast

try:
    from .command_source_validation_core_runner import FUNCTION_STATEMENTS
    from .command_source_validation_core_scan import _scan_statement_calls
    from .command_source_validation_taint import bind_assignment_targets, classify_expression
except ImportError:  # pragma: no cover
    from command_source_validation_core_runner import FUNCTION_STATEMENTS
    from command_source_validation_core_scan import _scan_statement_calls
    from command_source_validation_taint import bind_assignment_targets, classify_expression

TRY_LIKE_STATEMENTS = (ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)


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
