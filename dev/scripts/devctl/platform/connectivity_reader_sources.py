"""AST source-evidence collection for ConnectivityRegistry readers."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, NamedTuple

from ..config import REPO_ROOT
from .ast_helpers import call_name

_READER_SOURCE_PATH_ROWS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "cli",
        (
            "dev/scripts/devctl/commands/vcs",
            "dev/scripts/devctl/control_plane",
        ),
    ),
    ("context_graph", ("dev/scripts/devctl/context_graph",)),
    ("render_surfaces", ("dev/scripts/devctl/platform/render.py",)),
    (
        "session_resume",
        (
            "dev/scripts/devctl/commands/governance/session_resume_support.py",
            "dev/scripts/devctl/commands/governance/session_resume_source_helpers.py",
        ),
    ),
    (
        "startup_context",
        (
            "dev/scripts/devctl/runtime/startup_context.py",
            "dev/scripts/devctl/runtime/startup_connectivity_registry.py",
        ),
    ),
    ("system_map_index", ("dev/scripts/devctl/platform/system_map.py",)),
    ("system_map_renderer", ("dev/scripts/devctl/platform/system_map.py",)),
)

READER_SOURCE_PATHS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    dict(_READER_SOURCE_PATH_ROWS)
)


class ReaderSourceEvidence(NamedTuple):
    """AST-visible names, calls, attrs, and string constants for one reader file."""

    path: str
    names: frozenset[str]
    calls: frozenset[str]
    attrs: frozenset[str]
    strings: frozenset[str]


def reader_evidence_by_id(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, tuple[ReaderSourceEvidence, ...]]:
    """Collect AST evidence for each reader source path."""
    return {
        reader_id: tuple(
            reader_source_evidence(path=path, repo_root=repo_root)
            for path in reader_paths(reader_id=reader_id, repo_root=repo_root)
        )
        for reader_id in READER_SOURCE_PATHS
    }


def reader_paths(*, reader_id: str, repo_root: Path = REPO_ROOT) -> tuple[Path, ...]:
    """Return concrete source paths associated with a registry reader id."""
    paths: list[Path] = []
    for rel in READER_SOURCE_PATHS.get(reader_id, ()):
        path = repo_root / rel
        if path.is_dir():
            paths.extend(
                sorted(p for p in path.rglob("*.py") if "/tests/" not in p.as_posix())
            )
            continue
        if path.exists():
            paths.append(path)
    return tuple(paths)


def reader_source_evidence(
    *,
    path: Path,
    repo_root: Path = REPO_ROOT,
) -> ReaderSourceEvidence:
    """Parse one reader file into bounded AST evidence."""
    rel_path = relative_reader_path(path=path, repo_root=repo_root)
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=rel_path)
    except (OSError, SyntaxError):
        return _empty_source_evidence(rel_path)
    return _reader_source_evidence_from_tree(path=rel_path, tree=tree)


def relative_reader_path(*, path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _empty_source_evidence(path: str) -> ReaderSourceEvidence:
    return ReaderSourceEvidence(
        path=path,
        names=frozenset(),
        calls=frozenset(),
        attrs=frozenset(),
        strings=frozenset(),
    )


def _reader_source_evidence_from_tree(
    *,
    path: str,
    tree: ast.AST,
) -> ReaderSourceEvidence:
    names: set[str] = set()
    calls: set[str] = set()
    attrs: set[str] = set()
    strings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
            continue
        if isinstance(node, ast.Attribute):
            attrs.add(node.attr)
            continue
        if isinstance(node, ast.Call):
            resolved_call_name = call_name(node.func)
            if resolved_call_name:
                calls.add(resolved_call_name)
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
    return ReaderSourceEvidence(
        path=path,
        names=frozenset(names),
        calls=frozenset(calls),
        attrs=frozenset(attrs),
        strings=frozenset(strings),
    )


__all__ = [
    "READER_SOURCE_PATHS",
    "ReaderSourceEvidence",
    "reader_evidence_by_id",
    "reader_paths",
    "reader_source_evidence",
    "relative_reader_path",
]
