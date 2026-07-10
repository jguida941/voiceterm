"""Shared Python module/import resolution helpers."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path
from typing import TypeVar

ResolvedTarget = TypeVar("ResolvedTarget")


def canonical_module_name(path: Path) -> str:
    """Return the canonical dotted module name for one repo-relative path."""
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def module_names_for_path(
    path: Path,
    *,
    target_roots: tuple[Path, ...] = (),
) -> tuple[str, ...]:
    """Return all valid module aliases for one repo-relative path."""
    candidates: list[str] = []
    seen: set[str] = set()

    canonical_name = canonical_module_name(path)
    if canonical_name:
        candidates.append(canonical_name)
        seen.add(canonical_name)

    for root in target_roots:
        if path != root and root not in path.parents:
            continue
        relative = path.relative_to(root)
        module_name = canonical_module_name(relative)
        if not module_name or module_name in seen:
            continue
        seen.add(module_name)
        candidates.append(module_name)

    return tuple(candidates)


def resolve_relative_module(
    *,
    current_module: str,
    current_is_package: bool,
    level: int,
    module: str | None,
) -> str | None:
    """Resolve one relative import into a dotted module path."""
    package_parts = [
        part
        for part in _package_name(
            current_module,
            is_package=current_is_package,
        ).split(".")
        if part
    ]
    if level > 1:
        up_levels = level - 1
        if up_levels > len(package_parts):
            return None
        package_parts = package_parts[:-up_levels]
    if module:
        package_parts.extend(part for part in module.split(".") if part)
    return ".".join(package_parts)


def candidate_python_modules(
    *,
    current_module: str,
    current_is_package: bool,
    node: ast.AST,
) -> list[str]:
    """Return candidate module names referenced by one import node."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    base = (
        resolve_relative_module(
            current_module=current_module,
            current_is_package=current_is_package,
            level=node.level,
            module=node.module,
        )
        if node.level
        else node.module
    )
    if not base:
        return []
    candidates = [base]
    for alias in node.names:
        if alias.name != "*":
            candidates.append(f"{base}.{alias.name}")
    return candidates


def resolve_module_target(
    candidate: str,
    module_index: Mapping[str, ResolvedTarget],
) -> ResolvedTarget | None:
    """Resolve a dotted module name to the nearest indexed target."""
    current = candidate
    while current:
        target = module_index.get(current)
        if target is not None:
            return target
        if "." not in current:
            break
        current = current.rsplit(".", 1)[0]
    return None


def _package_name(module_name: str, *, is_package: bool) -> str:
    if is_package:
        return module_name
    if "." not in module_name:
        return ""
    return module_name.rsplit(".", 1)[0]
