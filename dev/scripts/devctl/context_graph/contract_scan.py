"""AST-backed typed-contract discovery helpers for context-graph."""

from __future__ import annotations

import ast
from pathlib import Path

_SCAN_ROOTS = (
    Path("dev/scripts/devctl/context_graph"),
    Path("dev/scripts/devctl/runtime"),
    Path("dev/scripts/devctl/platform"),
    Path("dev/scripts/devctl/governance"),
    Path("dev/scripts/devctl/commands/governance"),
)
_CONTRACT_SUFFIXES = (
    "Authority",
    "Candidate",
    "Catalog",
    "Contract",
    "Decision",
    "Packet",
    "Record",
    "Ref",
    "Snapshot",
    "State",
)
_EXTRA_DISCOVERY_CONTRACTS = frozenset(
    {
        "GuardPromotionCandidate",
        "PlanningIRSnapshot",
        "SessionPacingState",
    }
)


def discoverable_contract_names() -> set[str]:
    """Return contract names explicitly advertised elsewhere in repo policy."""
    contract_names = set(_EXTRA_DISCOVERY_CONTRACTS)

    try:
        from ..platform.contract_definitions import shared_contracts

        contract_names.update(spec.contract_id for spec in shared_contracts())
    # broad-except: allow reason=platform contract registry may be absent in sparse/adopted repos fallback=keep AST discovery limited to explicit extras and suffix heuristics.
    except Exception:
        pass

    try:
        from ..governance.system_catalog_bootstrap import collect_bootstrap_commands

        for entry in collect_bootstrap_commands():
            contract_names.update(entry.contract_ids)
    # broad-except: allow reason=bootstrap command registry is optional during partial/adopted repo scans fallback=preserve AST discovery via explicit extras and suffix heuristics.
    except Exception:
        pass

    return contract_names


def iter_dataclass_defs(repo_root: Path) -> list[tuple[str, ast.ClassDef]]:
    """Yield repo-relative paths plus top-level dataclass class defs."""
    discovered: list[tuple[str, ast.ClassDef]] = []
    for rel_root in _SCAN_ROOTS:
        root = repo_root / rel_root
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            rel_path = path.relative_to(repo_root).as_posix()
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            for stmt in tree.body:
                if isinstance(stmt, ast.ClassDef) and is_dataclass(stmt):
                    discovered.append((rel_path, stmt))
    return discovered


def is_dataclass(class_def: ast.ClassDef) -> bool:
    """Return True when the class uses a dataclass decorator."""
    for decorator in class_def.decorator_list:
        target = decorator
        if isinstance(target, ast.Call):
            target = target.func
        if isinstance(target, ast.Name) and target.id == "dataclass":
            return True
        if isinstance(target, ast.Attribute) and target.attr == "dataclass":
            return True
    return False


def should_index_contract(class_name: str, contract_names: set[str]) -> bool:
    """Keep discovery focused on contract-like dataclasses."""
    if not class_name or class_name.startswith("_"):
        return False
    if class_name in contract_names:
        return True
    return class_name.endswith(_CONTRACT_SUFFIXES)


def field_names(class_def: ast.ClassDef) -> tuple[str, ...]:
    """Return public dataclass field names in source order."""
    names: list[str] = []
    for stmt in class_def.body:
        name = field_name(stmt)
        if not name or name.startswith("_") or name in names:
            continue
        names.append(name)
    return tuple(names)


def field_name(stmt: ast.stmt) -> str:
    """Extract a public field name from a class statement when present."""
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        return stmt.target.id
    if isinstance(stmt, ast.Assign) and stmt.targets:
        target = stmt.targets[0]
        if isinstance(target, ast.Name):
            return target.id
    return ""
