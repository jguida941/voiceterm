"""Small file-hash helpers shared by runtime reducers."""

from __future__ import annotations

import hashlib
from pathlib import Path


def hash_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def existing_file_hashes(
    repo_root: Path,
    relative_paths: tuple[str, ...],
) -> dict[str, str]:
    """Return sha256 hashes for existing repo-relative files."""
    hashes: dict[str, str] = {}
    for relative in relative_paths:
        path = repo_root / relative
        if not path.exists() or not path.is_file():
            continue
        hashes[relative] = hash_bytes(path.read_bytes())
    return hashes


__all__ = ["existing_file_hashes", "hash_bytes"]
