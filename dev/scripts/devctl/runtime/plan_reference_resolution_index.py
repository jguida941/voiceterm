"""Index-building helpers for typed plan-reference resolution."""

from __future__ import annotations

import re
from collections.abc import Iterable


def append_paths(
    mapping: dict[str, list[str]],
    token: str,
    paths: Iterable[str],
) -> None:
    if not token:
        return
    bucket = mapping.setdefault(token, [])
    for path in paths:
        normalized = str(path or "").strip()
        if normalized and normalized not in bucket:
            bucket.append(normalized)


def append_bare_mp_id(
    mapping: dict[str, list[str]],
    token: str,
    relative_path: str,
    *,
    normalize_token,
) -> None:
    bare = bare_mp_id(token, normalize_token=normalize_token)
    if bare:
        append_paths(mapping, bare, (relative_path,))


def bare_mp_id(token: str, *, normalize_token) -> str:
    match = re.match(r"^MP(?P<num>\d+)-P\d+(?:-T\d+)?$", normalize_token(token))
    if match is None:
        return ""
    return f"MP-{match.group('num')}"
