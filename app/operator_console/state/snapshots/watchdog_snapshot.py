"""Cached watchdog-summary loader for the Operator Console."""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from dev.scripts.devctl.watchdog import (
    WatchdogSummaryArtifact,
    load_watchdog_summary_artifact,
)

DEFAULT_WATCHDOG_SUMMARY_REL = "dev/reports/data_science/latest/summary.json"
_CACHE_LOCK = Lock()
_CACHE: dict[str, tuple[int | None, WatchdogSummaryArtifact]] = {}


def load_watchdog_analytics_snapshot(repo_root: Path) -> WatchdogSummaryArtifact:
    """Return the latest repo-owned watchdog summary artifact."""
    if not repo_root.exists():
        return load_watchdog_summary_artifact(repo_root / DEFAULT_WATCHDOG_SUMMARY_REL)
    summary_path = repo_root / DEFAULT_WATCHDOG_SUMMARY_REL
    cache_key = str(repo_root.resolve())
    signature = _mtime_ns(summary_path)
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None and cached[0] == signature:
            return cached[1]
    snapshot = load_watchdog_summary_artifact(summary_path)
    with _CACHE_LOCK:
        _CACHE[cache_key] = (signature, snapshot)
    return snapshot


def _mtime_ns(path: Path) -> int | None:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None
