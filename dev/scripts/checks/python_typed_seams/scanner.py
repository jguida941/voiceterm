"""Shared AST scanner for fixed-shape `object` + `getattr()` seams."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ObjectGetattrFinding:
    function_name: str
    function_line: int
    param_name: str
    getattr_count: int
    attr_names: tuple[str, ...]
    hit_lines: tuple[int, ...]


def _annotation_is_object(annotation: ast.expr | None) -> bool:
    if isinstance(annotation, ast.Name):
        return annotation.id == "object"
    if isinstance(annotation, ast.Constant):
        return annotation.value == "object"
    return False


def _object_param_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...]:
    names: list[str] = []
    for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
        if _annotation_is_object(arg.annotation):
            names.append(arg.arg)
    if node.args.vararg and _annotation_is_object(node.args.vararg.annotation):
        names.append(node.args.vararg.arg)
    if node.args.kwarg and _annotation_is_object(node.args.kwarg.annotation):
        names.append(node.args.kwarg.arg)
    return tuple(names)


def _string_literal(value: ast.expr | None) -> str | None:
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


def _iter_function_body_nodes(node: ast.FunctionDef | ast.AsyncFunctionDef):
    stack = list(reversed(node.body))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield child
        stack.extend(reversed(list(ast.iter_child_nodes(child))))


def scan_object_param_getattr_functions(
    text: str | None,
) -> tuple[ObjectGetattrFinding, ...]:
    if text is None:
        return ()
    tree = ast.parse(text)
    findings: list[ObjectGetattrFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        object_params = _object_param_names(node)
        if not object_params:
            continue
        hits_by_param: dict[str, list[tuple[str, int]]] = {
            name: [] for name in object_params
        }
        for child in _iter_function_body_nodes(node):
            if not isinstance(child, ast.Call):
                continue
            if not isinstance(child.func, ast.Name) or child.func.id != "getattr":
                continue
            if len(child.args) < 2 or not isinstance(child.args[0], ast.Name):
                continue
            param_name = child.args[0].id
            if param_name not in hits_by_param:
                continue
            attr_name = _string_literal(child.args[1])
            if attr_name is None:
                continue
            hits_by_param[param_name].append((attr_name, child.lineno))
        for param_name, hits in hits_by_param.items():
            if not hits:
                continue
            findings.append(
                ObjectGetattrFinding(
                    function_name=node.name,
                    function_line=node.lineno,
                    param_name=param_name,
                    getattr_count=len(hits),
                    attr_names=tuple(attr for attr, _ in hits),
                    hit_lines=tuple(line for _, line in hits),
                )
            )
    findings.sort(key=lambda row: (row.function_name, row.function_line, row.param_name))
    return tuple(findings)


def parse_object_getattr_hits(text: str) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "function_name": finding.function_name,
            "function_line": finding.function_line,
            "param_name": finding.param_name,
            "getattr_count": finding.getattr_count,
            "attr_names": finding.attr_names,
            "hit_lines": finding.hit_lines,
        }
        for finding in scan_object_param_getattr_functions(text)
    )
