"""Pytest class node helpers for FeatureProofReceipt evidence."""

from __future__ import annotations

import ast


def class_test_refs(relpath: str, node: ast.ClassDef) -> tuple[str, ...]:
    refs: list[str] = []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_test_function(child.name):
                refs.append(f"{relpath}::{node.name}::{child.name}")
    return tuple(refs)


def is_test_class(node: ast.ClassDef) -> bool:
    return node.name.startswith("Test") or _inherits_unittest_test_case(node)


def _inherits_unittest_test_case(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Attribute) and base.attr == "TestCase":
            return True
        if isinstance(base, ast.Name) and base.id == "TestCase":
            return True
    return False


def _is_test_function(name: str) -> bool:
    return name.startswith("test_")


__all__ = [
    "class_test_refs",
    "is_test_class",
]
