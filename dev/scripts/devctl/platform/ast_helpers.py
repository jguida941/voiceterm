"""Small AST helpers shared by platform tooling."""

from __future__ import annotations

import ast


def call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""
