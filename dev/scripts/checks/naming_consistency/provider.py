"""Provider-token helpers for naming-consistency checks."""

from __future__ import annotations

import re
from pathlib import Path


def _extract_provider_label_tokens(pattern: object) -> set[str]:
    if not isinstance(pattern, str):
        return set()
    grouped = re.search(r"\(\?:([^)]+)\)", pattern)
    source = grouped.group(1) if grouped else pattern
    tokens: set[str] = set()
    for item in source.split("|"):
        candidate = item.strip()
        if re.fullmatch(r"[a-z][a-z0-9]*", candidate):
            tokens.add(candidate)
    return tokens


def _parse_isolation_provider_tokens(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"PROVIDER_LABEL_PATTERN\s*=\s*r?['\"]([^'\"]+)['\"]", text)
    if match:
        return _extract_provider_label_tokens(match.group(1))
    compiled_match = re.search(
        r"PROVIDER_LABEL_PATTERN\s*=\s*re\.compile\(\s*r?['\"]([^'\"]+)['\"]",
        text,
    )
    return (
        _extract_provider_label_tokens(compiled_match.group(1))
        if compiled_match
        else set()
    )
