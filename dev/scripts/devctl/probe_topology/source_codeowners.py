"""CODEOWNERS helpers for probe topology."""

from __future__ import annotations

import fnmatch

from .source_paths import repo_root


def parse_codeowners_rules() -> list[tuple[str, list[str]]]:
    path = repo_root() / ".github" / "CODEOWNERS"
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
