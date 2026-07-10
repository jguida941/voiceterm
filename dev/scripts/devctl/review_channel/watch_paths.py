"""Stable identity and path helpers for review-channel watcher state."""

from __future__ import annotations

import re
from pathlib import Path


def watch_state_path(
    *,
    artifact_root: Path,
    target: str,
    status_filter: str,
) -> Path:
    return (
        artifact_root
        / "watchers"
        / f"{watch_key(target=target, status_filter=status_filter)}.json"
    )


def watch_key(*, target: str, status_filter: str) -> str:
    safe_target = _slug(target or "all-targets")
    safe_status = _slug(status_filter or "all-statuses")
    return f"watch_{safe_target}__{safe_status}"


def _slug(value: str) -> str:
    collapsed = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return collapsed or "unknown"
