"""Import parsing helpers for the platform-layer boundary guard."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ImportHit:
    import_name: str
    lineno: int


def parse_import_hits(text: str, *, relative_path: Path) -> tuple[ImportHit, ...]:
    tree = ast.parse(text)
    hits: list[ImportHit] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hits.append(ImportHit(import_name=alias.name, lineno=node.lineno))
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            hits.extend(
                _relative_import_hits(
                    relative_path=relative_path,
                    level=node.level,
                    module=node.module,
                    aliases=tuple(alias.name for alias in node.names),
                    lineno=node.lineno,
                )
            )
            continue
        if not node.module:
            continue
        if any(alias.name == "*" for alias in node.names):
            hits.append(ImportHit(import_name=node.module, lineno=node.lineno))
            continue
        for alias in node.names:
            hits.append(
                ImportHit(
                    import_name=f"{node.module}.{alias.name}",
                    lineno=node.lineno,
                )
            )
    return tuple(hits)


def _relative_import_hits(
    *,
    relative_path: Path,
    level: int,
    module: str | None,
    aliases: tuple[str, ...],
    lineno: int,
) -> tuple[ImportHit, ...]:
    if "*" in aliases:
        resolved = _resolve_relative_import(
            relative_path=relative_path,
            level=level,
            module=module,
        )
        return (ImportHit(import_name=resolved, lineno=lineno),) if resolved else ()
    hits: list[ImportHit] = []
    for alias_name in aliases:
        resolved = _resolve_relative_import(
            relative_path=relative_path,
            level=level,
            module=module,
            alias_name=alias_name,
        )
        if resolved:
            hits.append(ImportHit(import_name=resolved, lineno=lineno))
    return tuple(hits)


def _package_parts_for_path(relative_path: Path) -> tuple[str, ...]:
    module_path = relative_path.with_suffix("")
    parts = module_path.parts
    if parts and parts[-1] == "__init__":
        return tuple(parts[:-1])
    return tuple(parts[:-1])


def _resolve_relative_import(
    *,
    relative_path: Path,
    level: int,
    module: str | None,
    alias_name: str | None = None,
) -> str:
    package_parts = _package_parts_for_path(relative_path)
    if level <= 0:
        base_parts = tuple(str(module or "").split(".")) if module else ()
    else:
        ascend = max(level - 1, 0)
        parent_parts = package_parts[: len(package_parts) - ascend] if ascend else package_parts
        module_parts = tuple(str(module or "").split(".")) if module else ()
        base_parts = parent_parts + module_parts
    if alias_name and alias_name != "*":
        return ".".join((*base_parts, alias_name))
    return ".".join(base_parts)
