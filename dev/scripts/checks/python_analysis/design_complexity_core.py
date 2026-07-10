"""Core helpers for check_python_design_complexity."""

from __future__ import annotations

import ast
from typing import Any

DEFAULT_MAX_BRANCHES = 30
DEFAULT_MAX_RETURNS = 10


def is_python_test_path(path) -> bool:
    normalized = f"/{path.as_posix()}/"
    name = path.name
    return "/tests/" in normalized or name.startswith("test_") or name.endswith("_test.py")


def _coerce_positive_int(value: Any, default: int) -> int:
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        return default
    return resolved if resolved > 0 else default


def resolve_thresholds(guard_config: dict[str, Any] | None) -> dict[str, int]:
    config = guard_config if isinstance(guard_config, dict) else {}
    return {
        "max_branches": _coerce_positive_int(
            config.get("max_branches"),
            DEFAULT_MAX_BRANCHES,
        ),
        "max_returns": _coerce_positive_int(
            config.get("max_returns"),
            DEFAULT_MAX_RETURNS,
        ),
    }


class _FunctionMetricsVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.branch_count = 0
        self.return_count = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # pragma: no cover - nested defs skipped
        del node
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # pragma: no cover - nested defs skipped
        del node
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # pragma: no cover - nested classes skipped
        del node
        return None

    def visit_Return(self, node: ast.Return) -> None:
        self.return_count += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.branch_count += 1 + len(node.handlers) + int(bool(node.orelse)) + int(bool(node.finalbody))
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        self.branch_count += max(1, len(node.cases))
        self.generic_visit(node)


class _FunctionCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.functions: dict[str, dict[str, int | str]] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        try:
            for child in node.body:
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                    self.visit(child)
        finally:
            self.stack.pop()

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        visitor = _FunctionMetricsVisitor()
        for statement in node.body:
            visitor.visit(statement)
        qualname = ".".join((*self.stack, node.name))
        self.functions[qualname] = {
            "name": node.name,
            "line": int(node.lineno),
            "branches": int(visitor.branch_count),
            "returns": int(visitor.return_count),
        }
        self.stack.append(node.name)
        try:
            for child in node.body:
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                    self.visit(child)
        finally:
            self.stack.pop()


def collect_excessive_functions(
    text: str | None,
    *,
    thresholds: dict[str, int],
) -> dict[str, dict[str, int | str]]:
    if text is None:
        return {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {}
    collector = _FunctionCollector()
    collector.visit(tree)
    return {
        qualname: metrics
        for qualname, metrics in collector.functions.items()
        if int(metrics["branches"]) > thresholds["max_branches"] or int(metrics["returns"]) > thresholds["max_returns"]
    }


def build_function_violation(
    *,
    qualname: str,
    current: dict[str, int | str],
    base: dict[str, int | str] | None,
    thresholds: dict[str, int],
) -> dict[str, Any] | None:
    reasons: list[str] = []
    branch_growth = 0
    return_growth = 0

    current_branches = int(current["branches"])
    current_returns = int(current["returns"])
    base_branches = int(base["branches"]) if isinstance(base, dict) else 0
    base_returns = int(base["returns"]) if isinstance(base, dict) else 0

    if current_branches > thresholds["max_branches"] and current_branches > base_branches:
        reasons.append("too_many_branches")
        branch_growth = current_branches - base_branches
    if current_returns > thresholds["max_returns"] and current_returns > base_returns:
        reasons.append("too_many_returns")
        return_growth = current_returns - base_returns

    if not reasons:
        return None

    return {
        "qualname": qualname,
        "name": str(current["name"]),
        "line": int(current["line"]),
        "reasons": reasons,
        "base": (
            {
                "branches": base_branches,
                "returns": base_returns,
            }
            if isinstance(base, dict)
            else None
        ),
        "current": {
            "branches": current_branches,
            "returns": current_returns,
        },
        "growth": {
            "branches": branch_growth,
            "returns": return_growth,
        },
    }
