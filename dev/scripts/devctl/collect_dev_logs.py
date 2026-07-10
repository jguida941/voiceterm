"""Helpers for summarizing guarded Dev Mode session logs."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import REPO_ROOT

DevLogSummary = dict[str, Any]
DevLogSessionRow = dict[str, Any]


def collect_dev_log_summary(
    dev_root: str | None = None, session_limit: int = 5
) -> dict[str, Any]:
    """Return aggregate summary for guarded Dev Mode JSONL sessions."""
    root = _resolve_dev_root(dev_root)
    sessions_dir = root / "sessions"
    limit = max(1, int(session_limit))

    summary = _new_dev_log_summary(root, sessions_dir)
    if not sessions_dir.is_dir():
        return summary

    scanned = _select_dev_log_session_files(summary, sessions_dir, limit)
    latency_sum = 0
    for path in scanned:
        session_row, session_latency_sum = _collect_dev_log_session(path, summary)
        summary["recent_sessions"].append(session_row)
        latency_sum += session_latency_sum

    _finalize_dev_log_summary(summary, latency_sum)
    return summary


def _new_dev_log_summary(root: Path, sessions_dir: Path) -> DevLogSummary:
    return {
        "dev_root": str(root),
        "sessions_dir": str(sessions_dir),
        "sessions_dir_exists": sessions_dir.is_dir(),
        "session_files_total": 0,
        "sessions_scanned": 0,
        "events_scanned": 0,
        "transcript_events": 0,
        "empty_events": 0,
        "error_events": 0,
        "total_words": 0,
        "latency_samples": 0,
        "avg_latency_ms": None,
        "parse_errors": 0,
        "latest_event_unix_ms": None,
        "recent_sessions": [],
    }


def _select_dev_log_session_files(
    summary: DevLogSummary, sessions_dir: Path, limit: int
) -> list[Path]:
    files = _session_files_sorted(sessions_dir)
    summary["session_files_total"] = len(files)
    scanned = files[:limit]
    summary["sessions_scanned"] = len(scanned)
    return scanned


def _collect_dev_log_session(
    path: Path, summary: DevLogSummary
) -> tuple[DevLogSessionRow, int]:
    session_row = _new_dev_log_session_row(path)
    session_latency_sum = 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                latency = _collect_dev_log_line(raw_line, session_row, summary)
                if latency is not None:
                    session_latency_sum += latency
    except OSError as exc:
        session_row["error"] = str(exc)

    _finalize_dev_log_session_row(session_row, session_latency_sum)
    return session_row, session_latency_sum


def _new_dev_log_session_row(path: Path) -> DevLogSessionRow:
    return {
        "file": path.name,
        "events": 0,
        "transcript_events": 0,
        "empty_events": 0,
        "error_events": 0,
        "latency_samples": 0,
        "avg_latency_ms": None,
        "parse_errors": 0,
    }


def _collect_dev_log_line(
    raw_line: str, session_row: DevLogSessionRow, summary: DevLogSummary
) -> int | None:
    line = raw_line.strip()
    if not line:
        return None

    session_row["events"] += 1
    summary["events_scanned"] += 1
    event = _parse_dev_log_event(line, session_row, summary)
    if event is None:
        return None

    _update_dev_log_kind_counts(event, session_row, summary)
    summary["total_words"] += _coerce_nonnegative_int(event.get("transcript_words"))
    latency = _record_dev_log_latency(event, session_row, summary)
    _update_dev_log_latest_timestamp(event, summary)
    return latency


def _parse_dev_log_event(
    line: str, session_row: DevLogSessionRow, summary: DevLogSummary
) -> dict[str, Any] | None:
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        _increment_dev_log_parse_error(session_row, summary)
        return None
    if not isinstance(event, dict):
        _increment_dev_log_parse_error(session_row, summary)
        return None
    return event


def _increment_dev_log_parse_error(
    session_row: DevLogSessionRow, summary: DevLogSummary
) -> None:
    session_row["parse_errors"] += 1
    summary["parse_errors"] += 1


def _update_dev_log_kind_counts(
    event: dict[str, Any], session_row: DevLogSessionRow, summary: DevLogSummary
) -> None:
    kind = str(event.get("kind", "")).strip().lower()
    if kind == "transcript":
        session_row["transcript_events"] += 1
        summary["transcript_events"] += 1
    elif kind == "empty":
        session_row["empty_events"] += 1
        summary["empty_events"] += 1
    elif kind == "error":
        session_row["error_events"] += 1
        summary["error_events"] += 1


def _record_dev_log_latency(
    event: dict[str, Any], session_row: DevLogSessionRow, summary: DevLogSummary
) -> int | None:
    latency = _coerce_nonnegative_int_or_none(event.get("latency_ms"))
    if latency is None:
        return None

    session_row["latency_samples"] += 1
    summary["latency_samples"] += 1
    return latency


def _update_dev_log_latest_timestamp(
    event: dict[str, Any], summary: DevLogSummary
) -> None:
    timestamp = _coerce_nonnegative_int_or_none(event.get("timestamp_unix_ms"))
    if timestamp is None:
        return

    latest_event = summary["latest_event_unix_ms"]
    if latest_event is None or timestamp > latest_event:
        summary["latest_event_unix_ms"] = timestamp


def _finalize_dev_log_session_row(
    session_row: DevLogSessionRow, session_latency_sum: int
) -> None:
    if session_row["latency_samples"] > 0:
        session_row["avg_latency_ms"] = int(
            session_latency_sum / session_row["latency_samples"]
        )


def _finalize_dev_log_summary(summary: DevLogSummary, latency_sum: int) -> None:
    if summary["latency_samples"] > 0:
        summary["avg_latency_ms"] = int(latency_sum / summary["latency_samples"])
    latest_ts = summary["latest_event_unix_ms"]
    if isinstance(latest_ts, int):
        summary["latest_event_iso"] = _unix_ms_to_iso(latest_ts)
    else:
        summary["latest_event_iso"] = None


def _resolve_dev_root(dev_root: str | None) -> Path:
    if dev_root:
        return Path(dev_root).expanduser()
    home = os.environ.get("HOME", "").strip()
    if home:
        return Path(home).expanduser() / ".voiceterm" / "dev"
    return REPO_ROOT / ".voiceterm" / "dev"


def _session_files_sorted(sessions_dir: Path) -> list[Path]:
    files = [path for path in sessions_dir.glob("session-*.jsonl") if path.is_file()]
    files.sort(
        key=lambda path: (path.stat().st_mtime_ns, path.name),
        reverse=True,
    )
    return files


def _coerce_nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    return 0


def _coerce_nonnegative_int_or_none(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    return None


def _unix_ms_to_iso(unix_ms: int) -> str:
    return datetime.fromtimestamp(unix_ms / 1000.0, tz=timezone.utc).isoformat()
