"""Rust module graph helpers for probe topology."""

from __future__ import annotations

import re
from pathlib import Path

from .source_paths import repo_relative, repo_root

RUST_USE_RE = re.compile(r"^\s*use\s+([^;]+);", re.MULTILINE)
RUST_MOD_RE = re.compile(r"^\s*(?:pub\s+)?mod\s+([a-zA-Z0-9_]+)\s*;", re.MULTILINE)


def rust_tokens_for_path(path: Path) -> tuple[str, ...]:
    rust_root = repo_root() / "rust" / "src"
    if not path.is_relative_to(rust_root):
        return ()
    parts = list(path.relative_to(rust_root).parts)
    if len(parts) >= 3 and parts[0] == "bin":
        parts = parts[2:]
    stem = path.stem
    if stem in {"lib", "main", "mod"}:
        parts = parts[:-1]
    elif parts:
        parts[-1] = stem
    return tuple(part for part in parts if part)


def build_rust_suffix_index(paths: list[Path]) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in paths:
        rel_path = repo_relative(path)
        tokens = rust_tokens_for_path(path)
        for offset in range(len(tokens)):
            suffix = "::".join(tokens[offset:])
            if suffix and suffix not in index:
                index[suffix] = rel_path
    return index


def normalize_rust_use_prefix(raw_expr: str) -> str:
    return raw_expr.split("{", 1)[0].strip().rstrip(":").strip()


def resolve_rust_target(
    *,
    rel_path: str,
    current_tokens: tuple[str, ...],
    raw_expr: str,
    suffix_index: dict[str, str],
) -> str | None:
    expr = normalize_rust_use_prefix(raw_expr)
    parts = [part for part in expr.split("::") if part]
    if not parts:
        return None
    if parts[0] == "crate":
        candidate = "::".join(parts[1:])
    elif parts[0] in {"super", "self"}:
        candidate = "::".join(current_tokens[:-1] + tuple(parts[1:]))
    else:
        candidate = "::".join(parts)
    target = suffix_index.get(candidate)
    if target == rel_path:
        return None
    return target


def resolve_rust_mod_target(rel_path: str, module_name: str) -> str | None:
    parent = (repo_root() / rel_path).parent
    for candidate in (
        parent / f"{module_name}.rs",
        parent / module_name / "mod.rs",
    ):
        if candidate.exists():
            return repo_relative(candidate)
    return None


def collect_rust_edges(
    paths: list[Path],
    suffix_index: dict[str, str],
) -> tuple[set[tuple[str, str, str]], list[str]]:
    edges: set[tuple[str, str, str]] = set()
    warnings: list[str] = []
    for path in paths:
        rel_path = repo_relative(path)
        current_tokens = rust_tokens_for_path(path)
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            warnings.append(f"{rel_path}: rust topology skipped ({exc})")
            continue
        for match in RUST_USE_RE.finditer(source):
            target = resolve_rust_target(
                rel_path=rel_path,
                current_tokens=current_tokens,
                raw_expr=match.group(1),
                suffix_index=suffix_index,
            )
            if target is not None:
                edges.add((rel_path, target, "rust_use"))
        for match in RUST_MOD_RE.finditer(source):
            target = resolve_rust_mod_target(rel_path, match.group(1))
            if target is not None and target != rel_path:
                edges.add((rel_path, target, "rust_mod"))
    return edges, warnings
