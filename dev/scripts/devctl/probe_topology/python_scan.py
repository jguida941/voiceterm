"""Python import graph helpers for probe topology."""

from __future__ import annotations

import ast
from pathlib import Path

from .source_paths import repo_relative, repo_root


def python_module_name(path: Path) -> str:
    rel = path.relative_to(repo_root()).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build_python_module_index(paths: list[Path]) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in paths:
        index[python_module_name(path)] = repo_relative(path)
    return index


def resolve_relative_python_module(
    current_module: str,
    module: str | None,
    level: int,
) -> str:
    if level <= 0:
        return module or ""
    package_parts = current_module.split(".")[:-1]
    trim = max(level - 1, 0)
    if trim:
        package_parts = package_parts[:-trim]
    base = ".".join(part for part in package_parts if part)
    if base and module:
        return f"{base}.{module}"
    return base or (module or "")


def candidate_python_modules(
    *,
    current_module: str,
    node: ast.AST,
) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    base = resolve_relative_python_module(current_module, node.module, node.level)
    if not base:
        return []
    candidates = [base]
    for alias in node.names:
        if alias.name != "*":
            candidates.append(f"{base}.{alias.name}")
    return candidates


def resolve_python_target(
    candidate: str,
    module_index: dict[str, str],
) -> str | None:
    current = candidate
    while current:
        target = module_index.get(current)
        if target is not None:
            return target
        if "." not in current:
            break
        current = current.rsplit(".", 1)[0]
    return None


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
