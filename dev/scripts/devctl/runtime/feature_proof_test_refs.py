"""Pytest node evidence extraction for FeatureProofReceipt tests_run fields."""

from __future__ import annotations

import ast
import re
import shlex
from collections.abc import Iterable
from pathlib import Path

from .feature_proof_test_class_refs import class_test_refs, is_test_class
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


def pytest_node_ref_candidates(values: Iterable[str]) -> tuple[str, ...]:
    """Return pytest node-looking refs found in command or node-id strings."""
    refs: list[str] = []
    for raw_value in values:
        refs.extend(_pytest_node_ref_candidates_from_text(coerce_string(raw_value)))
    return unique_refs(refs)


def pytest_node_ref_resolves(
    ref: str,
    *,
    repo_root: Path | None,
) -> bool:
    """Return whether a pytest node id names a test collected from its file."""
    if repo_root is None:
        return False
    normalized = _normalize_pytest_node_ref(ref, repo_root=repo_root)
    if not normalized:
        return False
    relpath = normalized.split("::", 1)[0]
    return normalized in _pytest_node_refs_for_file(repo_root / relpath, relpath)


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
        if isinstance(node, ast.ClassDef) and is_test_class(node):
            refs.extend(class_test_refs(relpath, node))
    return tuple(refs)


_PYTEST_NODE_REF_RE = re.compile(
    r"(?P<ref>(?:[A-Za-z0-9_./-]+\.py)(?:::[A-Za-z0-9_][A-Za-z0-9_\[\].-]*)+)"
)


def _pytest_node_ref_candidates_from_text(text: str) -> tuple[str, ...]:
    if not text:
        return ()
    refs: list[str] = []
    for token in _text_tokens(text):
        refs.extend(match.group("ref") for match in _PYTEST_NODE_REF_RE.finditer(token))
    return unique_refs(refs)


def _text_tokens(text: str) -> tuple[str, ...]:
    tokens = [text]
    try:
        tokens.extend(shlex.split(text))
    except ValueError:
        tokens.extend(text.split())
    return tuple(tokens)


def _normalize_pytest_node_ref(ref: str, *, repo_root: Path) -> str:
    text = coerce_string(ref).strip()
    if text.startswith("path:"):
        text = text.removeprefix("path:")
    if "::" not in text:
        return ""
    raw_path, *raw_node_parts = text.split("::")
    node_parts = tuple(
        _strip_paramization(part.strip())
        for part in raw_node_parts
        if part.strip()
    )
    if not node_parts:
        return ""
    relpath = _display_path(raw_path, repo_root=repo_root)
    if not _looks_like_pytest_file(relpath):
        return ""
    return "::".join((relpath, *node_parts))


def _strip_paramization(node_part: str) -> str:
    return node_part.split("[", 1)[0]


def _is_test_function(name: str) -> bool:
    return name.startswith("test_")


__all__ = [
    "pytest_node_ref_candidates",
    "pytest_node_ref_resolves",
    "pytest_node_refs_for_paths",
]
