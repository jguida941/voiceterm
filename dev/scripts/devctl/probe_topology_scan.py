"""Source scanning utilities for probe topology artifacts."""

from __future__ import annotations

import ast
import fnmatch
import re
from pathlib import Path

from .collect import collect_git_status
from .config import REPO_ROOT

SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "target",
    "venv",
}
RUST_USE_RE = re.compile(r"^\s*use\s+([^;]+);", re.MULTILINE)
RUST_MOD_RE = re.compile(r"^\s*(?:pub\s+)?mod\s+([a-zA-Z0-9_]+)\s*;", re.MULTILINE)


def repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def iter_source_files() -> dict[str, list[Path]]:
    buckets: dict[str, list[Path]] = {"python": [], "rust": []}
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(REPO_ROOT).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        if path.suffix == ".py":
            buckets["python"].append(path)
        elif path.suffix == ".rs":
            buckets["rust"].append(path)
    return buckets


def python_module_name(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT).with_suffix("")
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


def rust_tokens_for_path(path: Path) -> tuple[str, ...]:
    rust_root = REPO_ROOT / "rust" / "src"
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
    parent = (REPO_ROOT / rel_path).parent
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


def parse_codeowners_rules() -> list[tuple[str, list[str]]]:
    path = REPO_ROOT / ".github" / "CODEOWNERS"
    if not path.exists():
        return []
    rules: list[tuple[str, list[str]]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            rules.append((parts[0], parts[1:]))
    return rules


def codeowners_match(pattern: str, rel_path: str) -> bool:
    normalized = rel_path.lstrip("/")
    if pattern == "*":
        return True
    if pattern.endswith("/"):
        prefix = pattern.lstrip("/").rstrip("/")
        return normalized.startswith(f"{prefix}/") or normalized == prefix
    return fnmatch.fnmatch(normalized, pattern.lstrip("/"))


def owners_for_path(rel_path: str, rules: list[tuple[str, list[str]]]) -> list[str]:
    matched: list[str] = []
    for pattern, owners in rules:
        if codeowners_match(pattern, rel_path):
            matched = owners
    return matched


def collect_changed_paths(
    since_ref: str | None,
    head_ref: str,
) -> tuple[set[str], list[str]]:
    status = collect_git_status(since_ref=since_ref, head_ref=head_ref)
    if "error" in status:
        return set(), [f"git change context unavailable: {status['error']}"]
    changes = status.get("changes", [])
    if not isinstance(changes, list):
        return set(), ["git change context unavailable: unexpected changes payload"]
    return {
        str(change.get("path") or "").strip()
        for change in changes
        if isinstance(change, dict) and str(change.get("path") or "").strip()
    }, []
