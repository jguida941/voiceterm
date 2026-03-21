"""Serialized markdown-bridge rewrite helpers."""

from __future__ import annotations

import fcntl
from collections.abc import Callable
from pathlib import Path


def rewrite_bridge_markdown(
    bridge_path: Path,
    *,
    transform: Callable[[str], str],
) -> str:
    """Rewrite the bridge file under an exclusive file lock.

    The markdown bridge is still a transitional surface, but repo-owned writes
    should not race each other while it remains live.
    """
    with bridge_path.open("r+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            original = handle.read()
            updated = transform(original)
            handle.seek(0)
            handle.write(updated)
            handle.truncate()
            handle.flush()
            return updated
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
