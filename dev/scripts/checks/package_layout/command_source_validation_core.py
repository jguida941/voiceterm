"""AST analysis for Python command-source validation."""

from __future__ import annotations

import ast

if __package__:
    from .command_source_validation_core_flow import _analyze_statements
    from .command_source_validation_core_runner import (
        _call_uses_command_runner,
        _collect_command_wrapper_names,
    )
    from .command_source_validation_taint import collect_import_bindings
else:  # pragma: no cover - standalone script fallback
    from command_source_validation_core_flow import _analyze_statements
    from command_source_validation_core_runner import (
        _call_uses_command_runner,
        _collect_command_wrapper_names,
    )
    from command_source_validation_taint import collect_import_bindings


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
