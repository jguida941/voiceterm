"""Session discovery helpers for the typed agent work-board."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from ..commands.rollout_tail.discovery import iter_session_files


def recent_sessions(
    *,
    provider: str,
    root: Path | None,
    cutoff_seconds: int,
) -> list[tuple[Path, str, str]]:
    if root is None or not root.exists():
        return []
    candidates = list(iter_session_files(provider, root))
    return attach_timestamps(recent_paths(candidates, cutoff_seconds=cutoff_seconds))


def recent_paths(paths: Iterable[Path], *, cutoff_seconds: int) -> list[Path]:
    now = datetime.now(tz=timezone.utc).timestamp()
    fresh: list[Path] = []
    for path in paths:
        try:
            stat = path.stat()
        except OSError:
            continue
        if now - stat.st_mtime <= cutoff_seconds:
            fresh.append(path)
    fresh.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return fresh


def attach_timestamps(paths: list[Path]) -> list[tuple[Path, str, str]]:
    rows: list[tuple[Path, str, str]] = []
    for path in paths:
        try:
            stat = path.stat()
        except OSError:
            continue
        started = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat()
        last_active = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        rows.append((path, started, last_active))
    return rows


def utc_iso_pair_for(path: Path) -> tuple[str, str]:
    try:
        stat = path.stat()
    except OSError:
        return "", ""
    started = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat()
    last_active = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    return started, last_active


def now_utc_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def seconds_between(start_iso: str, end_iso: str) -> int:
    if not start_iso or not end_iso:
        return 0
    try:
        start = datetime.fromisoformat(start_iso)
        end = datetime.fromisoformat(end_iso)
    except ValueError:
        return 0
    delta = (end - start).total_seconds()
    return max(0, int(delta))
