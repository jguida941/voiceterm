"""Build symbol/path indexes for the plan GOLD-claim resolver."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

DEFAULT_CODE_ROOTS: tuple[str, ...] = ("dev/scripts",)
CONTRACT_REGISTRY_REL = "dev/state/contract_registry.jsonl"
PROPOSAL_STUB_PATHS = frozenset(
    {
        "dev/scripts/devctl/runtime/governance_proposed_contracts.py",
    }
)


@dataclass(frozen=True)
class SymbolIndex:
    symbols: frozenset[str]
    shipped_symbols: frozenset[str]
    proposal_stub_symbols: frozenset[str]
    exact_paths: frozenset[str]
    basenames: frozenset[str]


def build_symbol_index(
    repo_root: Path = REPO_ROOT,
    *,
    code_roots: Sequence[str] = DEFAULT_CODE_ROOTS,
    contract_registry_rel: str = CONTRACT_REGISTRY_REL,
) -> SymbolIndex:
    symbols: set[str] = set()
    shipped_symbols: set[str] = set()
    proposal_stub_symbols: set[str] = set()
    exact_paths: set[str] = set()
    basenames: set[str] = set()

    for path in repo_root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        exact_paths.add(_relative_path(repo_root, path))
        basenames.add(path.name)

    for root in code_roots:
        root_path = repo_root / root
        if not root_path.exists():
            continue
        paths = [root_path] if root_path.is_file() else root_path.rglob("*")
        for path in paths:
            _add_python_file_symbols(
                repo_root=repo_root,
                path=path,
                symbols=symbols,
                shipped_symbols=shipped_symbols,
                proposal_stub_symbols=proposal_stub_symbols,
            )

    registry_path = repo_root / contract_registry_rel
    _add_registry_symbols(
        registry_path=registry_path,
        symbols=symbols,
        shipped_symbols=shipped_symbols,
        proposal_stub_symbols=proposal_stub_symbols,
    )

    return SymbolIndex(
        symbols=frozenset(symbols),
        shipped_symbols=frozenset(shipped_symbols),
        proposal_stub_symbols=frozenset(proposal_stub_symbols),
        exact_paths=frozenset(exact_paths),
        basenames=frozenset(basenames),
    )


def _add_python_file_symbols(
    *,
    repo_root: Path,
    path: Path,
    symbols: set[str],
    shipped_symbols: set[str],
    proposal_stub_symbols: set[str],
) -> None:
    if not path.is_file() or "__pycache__" in path.parts or path.suffix != ".py":
        return
    rel = _relative_path(repo_root, path)
    path_symbols = _python_symbols(path)
    symbols.update(path_symbols)
    if rel in PROPOSAL_STUB_PATHS:
        proposal_stub_symbols.update(path_symbols)
    else:
        shipped_symbols.update(path_symbols)


def _add_registry_symbols(
    *,
    registry_path: Path,
    symbols: set[str],
    shipped_symbols: set[str],
    proposal_stub_symbols: set[str],
) -> None:
    for row in _read_jsonl_dicts(registry_path):
        for field in ("contract_id", "registered_contract_id"):
            value = row.get(field)
            if not isinstance(value, str) or not value:
                continue
            symbols.add(value)
            if row.get("python_owner_path") in PROPOSAL_STUB_PATHS:
                proposal_stub_symbols.add(value)
            else:
                shipped_symbols.add(value)


def _read_jsonl_dicts(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _python_symbols(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    except (SyntaxError, UnicodeDecodeError):
        return set()
    symbols: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                symbols.update(_assignment_names(target))
        elif isinstance(node, ast.AnnAssign):
            symbols.update(_assignment_names(node.target))
    return symbols


def _assignment_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for item in target.elts:
            names.update(_assignment_names(item))
        return names
    return set()


def _relative_path(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()
