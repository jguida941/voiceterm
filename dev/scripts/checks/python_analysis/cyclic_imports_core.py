"""Core helpers for check_python_cyclic_imports."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

try:
    from .cyclic_imports_graph import (
        build_import_graph,
        cycle_signature,
        strongly_connected_components,
    )
except ImportError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.python_analysis.cyclic_imports_graph import (
        build_import_graph,
        cycle_signature,
        strongly_connected_components,
    )


@dataclass(frozen=True)
class CycleGraphInputs:
    base_paths: list[Path]
    current_paths: list[Path]
    base_map: dict[Path, Path] | None


@dataclass(frozen=True)
class CycleReportInputs:
    candidate_paths: list[Path]
    graph_inputs: CycleGraphInputs
    base_text_by_path: dict[str, str | None]
    current_text_by_path: dict[str, str | None]
    mode: str
    target_roots: tuple[Path, ...]


def is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_") or path.name.endswith("_test.py")


def normalize_repo_path(path: Path, repo_root: Path) -> Path:
    try:
        return path.relative_to(repo_root)
    except ValueError:
        return path


def coerce_ignored_paths(
    *,
    repo_root: Path,
    resolve_guard_config_fn: Callable[[str, Path], dict],
) -> tuple[Path, ...]:
    config = resolve_guard_config_fn("python_cyclic_imports", repo_root)
    raw_paths = config.get("ignored_paths")
    if not isinstance(raw_paths, list):
        return ()
    ignored: list[Path] = []
    seen: set[Path] = set()
    for raw_path in raw_paths:
        text = str(raw_path or "").strip()
        if not text:
            continue
        path = normalize_repo_path(Path(text), repo_root)
        if path in seen:
            continue
        seen.add(path)
        ignored.append(path)
    return tuple(ignored)


def coerce_ignored_cycle_signatures(
    *,
    repo_root: Path,
    resolve_guard_config_fn: Callable[[str, Path], dict],
) -> set[tuple[str, ...]]:
    config = resolve_guard_config_fn("python_cyclic_imports", repo_root)
    raw_cycles = config.get("ignored_cycles")
    if not isinstance(raw_cycles, list):
        return set()
    signatures: set[tuple[str, ...]] = set()
    for raw_cycle in raw_cycles:
        if not isinstance(raw_cycle, list):
            continue
        members = [
            normalize_repo_path(Path(str(raw_path).strip()), repo_root).as_posix()
            for raw_path in raw_cycle
            if str(raw_path).strip()
        ]
        if len(members) > 1:
            signatures.add(tuple(sorted(members)))
    return signatures


def is_ignored_path(path: Path, ignored_paths: tuple[Path, ...]) -> bool:
    return any(path == ignored or ignored in path.parents for ignored in ignored_paths)


def list_python_paths_from_worktree(
    *,
    repo_root: Path,
    target_roots: tuple[Path, ...],
    ignored_paths: tuple[Path, ...],
) -> list[Path]:
    paths: set[Path] = set()
    for root in target_roots:
        absolute_root = repo_root / root
        if not absolute_root.is_dir():
            continue
        for candidate in absolute_root.rglob("*.py"):
            relative = candidate.relative_to(repo_root)
            if is_test_path(relative) or is_ignored_path(relative, ignored_paths):
                continue
            paths.add(relative)
    return sorted(paths)


def list_python_paths_from_ref(
    *,
    ref: str,
    run_git_fn,
    target_roots: tuple[Path, ...],
    ignored_paths: tuple[Path, ...],
) -> list[Path]:
    if not target_roots:
        return []
    command = [
        "git",
        "ls-tree",
        "-r",
        "--name-only",
        ref,
        "--",
        *(root.as_posix() for root in target_roots),
    ]
    paths: set[Path] = set()
    for raw_line in run_git_fn(command).stdout.splitlines():
        text = raw_line.strip()
        if not text:
            continue
        path = Path(text)
        if path.suffix != ".py":
            continue
        if is_test_path(path) or is_ignored_path(path, ignored_paths):
            continue
        paths.add(path)
    return sorted(paths)


def build_cycle_report(
    *,
    repo_root: Path,
    inputs: CycleReportInputs,
    resolve_guard_config_fn: Callable[[str, Path], dict],
) -> dict:
    ignored_paths = coerce_ignored_paths(
        repo_root=repo_root,
        resolve_guard_config_fn=resolve_guard_config_fn,
    )
    ignored_cycle_signatures = coerce_ignored_cycle_signatures(
        repo_root=repo_root,
        resolve_guard_config_fn=resolve_guard_config_fn,
    )
    changed_python_paths: set[Path] = set()
    files_skipped_non_python = 0
    files_skipped_tests = 0

    for raw_path in inputs.candidate_paths:
        path = normalize_repo_path(raw_path, repo_root)
        if path.suffix != ".py":
            files_skipped_non_python += 1
            continue
        if not any(path == root or root in path.parents for root in inputs.target_roots):
            files_skipped_non_python += 1
            continue
        if is_ignored_path(path, ignored_paths):
            files_skipped_non_python += 1
            continue
        if is_test_path(path):
            files_skipped_tests += 1
            continue
        changed_python_paths.add(path)

    normalized_base_paths = [
        normalize_repo_path(path, repo_root)
        for path in inputs.graph_inputs.base_paths
        if not is_ignored_path(normalize_repo_path(path, repo_root), ignored_paths)
    ]
    normalized_current_paths = [
        normalize_repo_path(path, repo_root)
        for path in inputs.graph_inputs.current_paths
        if not is_ignored_path(normalize_repo_path(path, repo_root), ignored_paths)
    ]
    normalized_base_map = {
        normalize_repo_path(path, repo_root): normalize_repo_path(base_path, repo_root)
        for path, base_path in (inputs.graph_inputs.base_map or {}).items()
    }

    base_graph = build_import_graph(
        paths=normalized_base_paths,
        text_by_path=inputs.base_text_by_path,
        target_roots=inputs.target_roots,
    )
    current_graph = build_import_graph(
        paths=normalized_current_paths,
        text_by_path=inputs.current_text_by_path,
        target_roots=inputs.target_roots,
    )
    base_signatures = {
        cycle_signature(component, rename_map={}) for component in strongly_connected_components(base_graph)
    }
    current_components = strongly_connected_components(current_graph)
    new_cycles = [
        component
        for component in current_components
        if any(path in changed_python_paths for path in component)
        and cycle_signature(component, rename_map=normalized_base_map) not in base_signatures
        and cycle_signature(component, rename_map={}) not in ignored_cycle_signatures
    ]

    path_cycles: dict[Path, list[list[str]]] = {}
    for component in new_cycles:
        cycle_members = [path.as_posix() for path in component]
        for path in component:
            path_cycles.setdefault(path, []).append(cycle_members)

    violations = [
        {
            "path": path.as_posix(),
            "growth": {"cyclic_imports": len(cycles)},
            "cycles": cycles,
        }
        for path, cycles in sorted(path_cycles.items(), key=lambda item: item[0].as_posix())
    ]

    return {
        "command": "check_python_cyclic_imports",
        "mode": inputs.mode,
        "ok": len(new_cycles) == 0,
        "files_changed": len(inputs.candidate_paths),
        "files_considered": len(changed_python_paths),
        "files_skipped_non_python": files_skipped_non_python,
        "files_skipped_tests": files_skipped_tests,
        "graph_python_files_base": len(normalized_base_paths),
        "graph_python_files_current": len(normalized_current_paths),
        "cycles_scanned": len(current_components),
        "ignored_paths": [path.as_posix() for path in ignored_paths],
        "ignored_cycle_count": len(ignored_cycle_signatures),
        "totals": {"cyclic_imports_growth": len(new_cycles)},
        "cycles": [{"members": [path.as_posix() for path in component]} for component in new_cycles],
        "violations": violations,
    }
