"""Graph-building helpers for Python cyclic-import detection."""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterable
from pathlib import Path

try:
    from dev.scripts.devctl.probe_topology.python_modules import (
        canonical_module_name,
        candidate_python_modules,
        module_names_for_path,
        resolve_module_target,
        resolve_relative_module as _resolve_relative_module,
    )
except ModuleNotFoundError:  # pragma: no cover
    repo_root = Path(__file__).resolve().parents[4]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    from dev.scripts.devctl.probe_topology.python_modules import (
        canonical_module_name,
        candidate_python_modules,
        module_names_for_path,
        resolve_module_target,
        resolve_relative_module as _resolve_relative_module,
    )


def module_names_for_path(
    path: Path,
    *,
    target_roots: tuple[Path, ...],
) -> tuple[str, ...]:
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
        if module_name and module_name not in seen:
            seen.add(module_name)
            candidates.append(module_name)
    return tuple(candidates)


def build_module_index(
    paths: Iterable[Path],
    *,
    target_roots: tuple[Path, ...],
) -> dict[str, Path]:
    module_index: dict[str, Path] = {}
    for path in paths:
        for module_name in module_names_for_path(path, target_roots=target_roots):
            module_index.setdefault(module_name, path)
    return module_index


def resolve_module(module_name: str, module_index: dict[str, Path]) -> Path | None:
    return resolve_module_target(module_name, module_index)


def resolve_relative_module(
    *,
    current_module: str,
    current_is_package: bool,
    level: int,
    module: str | None,
) -> str | None:
    return _resolve_relative_module(
        current_module=current_module,
        current_is_package=current_is_package,
        level=level,
        module=module,
    )


def top_level_dependencies(
    text: str | None,
    *,
    current_module: str,
    current_is_package: bool,
    module_index: dict[str, Path],
) -> set[Path]:
    if text is None:
        return set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()

    dependencies: set[Path] = set()
    for node in tree.body:
        for candidate in candidate_python_modules(
            current_module=current_module,
            current_is_package=current_is_package,
            node=node,
        ):
            target = resolve_module(candidate, module_index)
            if target is not None:
                dependencies.add(target)
    return dependencies


def build_import_graph(
    *,
    paths: list[Path],
    text_by_path: dict[str, str | None],
    target_roots: tuple[Path, ...],
) -> dict[Path, set[Path]]:
    module_index = build_module_index(paths, target_roots=target_roots)
    graph: dict[Path, set[Path]] = {}
    for path in paths:
        dependencies = top_level_dependencies(
            text_by_path.get(path.as_posix()),
            current_module=canonical_module_name(path),
            current_is_package=path.name == "__init__.py",
            module_index=module_index,
        )
        graph[path] = {target for target in dependencies if target != path}
    return graph


def strongly_connected_components(graph: dict[Path, set[Path]]) -> list[tuple[Path, ...]]:
    index = 0
    indices: dict[Path, int] = {}
    lowlinks: dict[Path, int] = {}
    stack: list[Path] = []
    on_stack: set[Path] = set()
    components: list[tuple[Path, ...]] = []

    def visit(node: Path) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in indices:
                visit(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbor])

        if lowlinks[node] != indices[node]:
            return

        component: list[Path] = []
        while stack:
            popped = stack.pop()
            on_stack.discard(popped)
            component.append(popped)
            if popped == node:
                break
        if len(component) > 1:
            components.append(tuple(sorted(component)))

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return sorted(components, key=lambda component: [path.as_posix() for path in component])


def cycle_signature(
    component: tuple[Path, ...],
    *,
    rename_map: dict[Path, Path],
) -> tuple[str, ...]:
    return tuple(sorted(rename_map.get(path, path).as_posix() for path in component))
