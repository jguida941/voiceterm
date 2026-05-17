"""Shared identity helpers for governance ledger artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


def hash_identity_parts(*parts: str | None) -> str:
    """Build a short deterministic identity from ordered string parts."""
    raw = "::".join(part or "" for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def normalize_identity_repo_path(
    value: object,
    *,
    repo_root: Path | None = None,
) -> str | None:
    """Drop absolute checkout roots from durable identity, keep relative subpaths."""
    text = _optional_text(value)
    if not text:
        return None
    candidate = Path(text).expanduser()
    if candidate.is_absolute():
        if repo_root is not None:
            try:
                relative = candidate.resolve().relative_to(repo_root.resolve())
            except (OSError, ValueError):
                return None
            relative_text = relative.as_posix()
            return None if relative_text in {"", "."} else relative_text
        return None
    normalized = candidate.as_posix()
    return None if normalized in {"", "."} else normalized


def normalize_identity_file_path(
    value: object,
    *,
    repo_root: Path | None = None,
    repo_path: str | None = None,
    field_name: str = "file_path",
) -> str:
    """Prefer repo-relative file paths for durable identities when possible.

    When no repo root can resolve the path, falls back to the file name
    rather than baking an absolute checkout path into the identity hash.
    """
    text = _required_text(value, field_name=field_name)
    candidate = Path(text).expanduser()
    if candidate.is_absolute():
        for root in _identity_roots(repo_root=repo_root, repo_path=repo_path):
            try:
                return candidate.resolve().relative_to(root.resolve()).as_posix()
            except (OSError, ValueError):
                continue
        return candidate.name
    return candidate.as_posix()


def _identity_roots(
    *,
    repo_root: Path | None,
    repo_path: str | None,
) -> tuple[Path, ...]:
    roots: list[Path] = []
    seen: set[str] = set()
    for candidate in (repo_root, Path(repo_path).expanduser() if repo_path else None):
        if candidate is None or not candidate.is_absolute():
            continue
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        roots.append(candidate)
    return tuple(roots)


def _required_text(value: object, *, field_name: str) -> str:
    text = _optional_text(value)
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
