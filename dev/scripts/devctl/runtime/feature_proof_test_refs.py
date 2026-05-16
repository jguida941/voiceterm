"""Pytest node evidence extraction for FeatureProofReceipt tests_run fields."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

from .ref_collections import unique_refs
from .value_coercion import coerce_string


def pytest_node_refs_for_paths(
    paths: Iterable[str],
    *,
    repo_root: Path | None,
) -> tuple[str, ...]:
    """Return concrete pytest node ids for repo-relative test files."""
    if repo_root is None:
        return ()
    refs: list[str] = []
    for raw_path in paths:
        relpath = _display_path(coerce_string(raw_path), repo_root=repo_root)
        if not _looks_like_pytest_file(relpath):
            continue
        refs.extend(_pytest_node_refs_for_file(repo_root / relpath, relpath))
    return unique_refs(refs)


def _display_path(raw_path: str, *, repo_root: Path) -> str:
    path = Path(raw_path)
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _looks_like_pytest_file(relpath: str) -> bool:
    path = Path(relpath)
    return path.suffix == ".py" and (
        path.name.startswith("test_") or "tests" in path.parts
    )


def _pytest_node_refs_for_file(path: Path, relpath: str) -> tuple[str, ...]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relpath)
    except (OSError, SyntaxError):
        return ()
    refs: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_test_function(node.name):
                refs.append(f"{relpath}::{node.name}")
            continue
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            refs.extend(_class_test_refs(relpath, node))
    return tuple(refs)


def _class_test_refs(relpath: str, node: ast.ClassDef) -> tuple[str, ...]:
    refs: list[str] = []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_test_function(child.name):
                refs.append(f"{relpath}::{node.name}::{child.name}")
    return tuple(refs)


def _is_test_function(name: str) -> bool:
    return name.startswith("test_")


__all__ = ["pytest_node_refs_for_paths"]
