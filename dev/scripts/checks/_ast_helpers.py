"""Shared AST utilities for dev/scripts/checks/ guards.

Hosts small helpers reused across multiple guard scripts so each guard does not
re-implement the same AST inspection logic. Closes the function_duplication
finding for `_call_name` between `check_action_result_status_domain.py` and
`runtime_bridge_projection_separation/command.py`.
"""

from __future__ import annotations

import ast


def _call_name(node: ast.AST) -> str:
    """Return the symbol name of a call target (Name) or attribute access (Attribute)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
