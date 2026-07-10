"""Python import graph helpers for probe topology."""

from __future__ import annotations

import ast
from pathlib import Path

from .python_modules import (
    candidate_python_modules as _candidate_python_modules,
    module_names_for_path,
    resolve_module_target,
    resolve_relative_module,
)
from .source_paths import repo_relative, repo_root


def python_module_name(path: Path) -> str:
    rel = path.relative_to(repo_root())
    aliases = module_names_for_path(rel)
    return aliases[0] if aliases else ""


def build_python_module_index(paths: list[Path]) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in paths:
        rel_path = repo_relative(path)
        for module_name in module_names_for_path(Path(rel_path)):
            index[module_name] = rel_path
    return index


def resolve_relative_python_module(
    current_module: str,
    module: str | None,
    level: int,
) -> str:
    return (
        resolve_relative_module(
            current_module=current_module,
            current_is_package=False,
            level=level,
            module=module,
        )
        or ""
    )


def candidate_python_modules(
    *,
    current_module: str,
    node: ast.AST,
) -> list[str]:
    return _candidate_python_modules(
        current_module=current_module,
        current_is_package=False,
        node=node,
    )


def resolve_python_target(
    candidate: str,
    module_index: dict[str, str],
) -> str | None:
    return resolve_module_target(candidate, module_index)


def collect_python_edges(
    paths: list[Path],
    module_index: dict[str, str],
) -> tuple[set[tuple[str, str, str]], list[str]]:
    edges: set[tuple[str, str, str]] = set()
    warnings: list[str] = []
    for path in paths:
        rel_path = repo_relative(path)
        current_module = python_module_name(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:
            warnings.append(f"{rel_path}: python topology skipped ({exc})")
            continue
        for node in ast.walk(tree):
            for candidate in candidate_python_modules(
                current_module=current_module,
                node=node,
            ):
                target = resolve_python_target(candidate, module_index)
                if target is None or target == rel_path:
                    continue
                kind = "python_import_from" if isinstance(node, ast.ImportFrom) else "python_import"
                edges.add((rel_path, target, kind))
    return edges, warnings
