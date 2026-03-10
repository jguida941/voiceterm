"""Cached quality-backlog snapshot collection for the Operator Console."""

from __future__ import annotations

from pathlib import Path
from threading import Lock
import time

from ..core.models import QualityBacklogSnapshot, QualityPrioritySignal, utc_timestamp

try:
    from dev.scripts.devctl.config import REPO_ROOT as DEVCTL_REPO_ROOT
    from dev.scripts.devctl.quality_backlog.report import collect_quality_backlog
except ImportError:  # pragma: no cover - repo import path should exist in-app
    DEVCTL_REPO_ROOT = None
    collect_quality_backlog = None

_CACHE_TTL_SECONDS = 120.0
_CACHE_LOCK = Lock()
_CACHE: dict[str, tuple[float, QualityBacklogSnapshot | None]] = {}


def collect_quality_backlog_snapshot(
    repo_root: Path,
    *,
    top_n: int = 20,
    include_tests: bool = False,
) -> QualityBacklogSnapshot | None:
    """Return a cached quality-backlog snapshot for the current repo."""
    if collect_quality_backlog is None or DEVCTL_REPO_ROOT is None:
        return None
    if repo_root.resolve() != Path(DEVCTL_REPO_ROOT).resolve():
        return None

    cache_key = str(repo_root.resolve())
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
            return cached[1]

    snapshot = _collect_uncached(top_n=top_n, include_tests=include_tests)
    with _CACHE_LOCK:
        _CACHE[cache_key] = (now, snapshot)
    return snapshot


def _collect_uncached(
    *,
    top_n: int,
    include_tests: bool,
) -> QualityBacklogSnapshot | None:
    if collect_quality_backlog is None:
        return None
    payload = collect_quality_backlog(
        top_n=max(0, int(top_n)),
        include_tests=include_tests,
    )
    if not isinstance(payload, dict):
        return None

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    checks = payload.get("checks")
    if not isinstance(checks, dict):
        checks = {}
    priorities = payload.get("priorities")
    if not isinstance(priorities, list):
        priorities = []

    failing_checks = tuple(
        sorted(
            key
            for key, row in checks.items()
            if isinstance(key, str)
            and isinstance(row, dict)
            and not bool(row.get("ok", False))
        )
    )
    top_priorities = tuple(_parse_priority_row(row) for row in priorities[:5])
    warnings = payload.get("warnings")
    errors = payload.get("errors")
    warning = _first_text_list_item(warnings) or _first_text_list_item(errors)

    return QualityBacklogSnapshot(
        captured_at_utc=_safe_text(payload.get("timestamp")) or utc_timestamp(),
        ok=bool(payload.get("ok", False)),
        source_files_scanned=_safe_int(summary.get("source_files_scanned")),
        guard_failures=_safe_int(summary.get("guard_failures")),
        critical_paths=_safe_int(summary.get("critical_paths")),
        high_paths=_safe_int(summary.get("high_paths")),
        medium_paths=_safe_int(summary.get("medium_paths")),
        low_paths=_safe_int(summary.get("low_paths")),
        ranked_paths=_safe_int(summary.get("ranked_paths")),
        failing_checks=failing_checks,
        top_priorities=top_priorities,
        warning=warning,
    )


def _parse_priority_row(row: object) -> QualityPrioritySignal:
    if not isinstance(row, dict):
        return QualityPrioritySignal(path="(unknown)", severity="unknown", score=0)
    signals = row.get("signals")
    if not isinstance(signals, list):
        signals = []
    return QualityPrioritySignal(
        path=_safe_text(row.get("path")) or "(unknown)",
        severity=_safe_text(row.get("severity")) or "unknown",
        score=_safe_int(row.get("score")),
        signals=tuple(
            text
            for text in (_safe_text(item) for item in signals[:6])
            if text is not None
        ),
    )


def _safe_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return 0
    return 0


def _safe_text(value: object) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def _first_text_list_item(value: object) -> str | None:
    if not isinstance(value, list):
        return None
    for item in value:
        text = _safe_text(item)
        if text is not None:
            return text
    return None
