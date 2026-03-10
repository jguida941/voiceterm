"""Read live review-channel session traces for Operator Console sessions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .session_trace_history import _sanitize_terminal_history
from .session_trace_terminal import _render_terminal_screen, _sanitize_terminal_screen

DEFAULT_SESSION_TRACE_DIR_CANDIDATES = (
    "dev/reports/review_channel/projections/latest/sessions",
    "dev/reports/review_channel/latest/sessions",
)
DEFAULT_SESSION_NAME_SUFFIX = "-conductor"


@dataclass(frozen=True)
class SessionTraceSnapshot:
    """One live review-channel session trace discovered on disk."""

    provider: str
    session_name: str
    capture_mode: str | None
    prepared_at: str | None
    updated_at: str | None
    metadata_path: str | None
    log_path: str
    tail_text: str
    screen_text: str
    history_text: str
    lane_count: int | None = None
    worker_budget: int | None = None


def load_live_session_trace(
    repo_root: Path,
    *,
    provider: str,
    review_full_path: Path | None = None,
    max_bytes: int = 256_000,
    max_lines: int = 160,
) -> SessionTraceSnapshot | None:
    """Return the latest tailed session trace when a real log exists."""
    metadata = _find_session_metadata(
        repo_root,
        provider=provider,
        review_full_path=review_full_path,
    )
    if metadata is None:
        return None
    log_path = _resolve_log_path(metadata=metadata, provider=provider)
    if log_path is None or not log_path.exists() or log_path.stat().st_size <= 0:
        return None
    raw_text = _read_tail_text(log_path, max_bytes=max_bytes)
    screen_text = _sanitize_terminal_screen(raw_text, max_lines=max_lines)
    history_text = _sanitize_terminal_history(raw_text, max_lines=max_lines)
    tail_text = history_text or screen_text
    if not tail_text.strip():
        return None
    return SessionTraceSnapshot(
        provider=provider,
        session_name=str(metadata.get("session_name") or f"{provider}{DEFAULT_SESSION_NAME_SUFFIX}"),
        capture_mode=_as_text(metadata.get("capture_mode")),
        prepared_at=_as_text(metadata.get("prepared_at")),
        updated_at=_mtime_iso_utc(log_path),
        metadata_path=_as_text(metadata.get("_metadata_path")),
        log_path=str(log_path),
        tail_text=tail_text,
        screen_text=screen_text,
        history_text=history_text,
        lane_count=_as_int(metadata.get("lane_count")),
        worker_budget=_as_int(metadata.get("worker_budget")),
    )


def _find_session_metadata(
    repo_root: Path,
    *,
    provider: str,
    review_full_path: Path | None,
) -> dict[str, object] | None:
    provider = provider.strip().lower()
    for session_dir in _candidate_session_dirs(repo_root, review_full_path=review_full_path):
        explicit = session_dir / f"{provider}{DEFAULT_SESSION_NAME_SUFFIX}.json"
        if explicit.exists():
            payload = _load_json_object(explicit)
            if payload is not None:
                return payload
        for candidate in sorted(session_dir.glob("*.json")):
            payload = _load_json_object(candidate)
            if payload is None:
                continue
            payload_provider = _as_text(payload.get("provider"))
            if payload_provider == provider:
                return payload
    return None


def _candidate_session_dirs(
    repo_root: Path,
    *,
    review_full_path: Path | None,
) -> tuple[Path, ...]:
    candidates: list[Path] = []
    if review_full_path is not None:
        candidates.append(review_full_path.parent / "sessions")
    for relative_path in DEFAULT_SESSION_TRACE_DIR_CANDIDATES:
        candidates.append(repo_root / relative_path)
    ordered: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(candidate)
    return tuple(ordered)


def _load_json_object(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    payload["_metadata_path"] = str(path)
    return payload


def _resolve_log_path(*, metadata: dict[str, object], provider: str) -> Path | None:
    log_path = _as_text(metadata.get("log_path"))
    if log_path:
        return Path(log_path)
    metadata_path = _as_text(metadata.get("_metadata_path"))
    if metadata_path is None:
        return None
    return Path(metadata_path).with_name(f"{provider}{DEFAULT_SESSION_NAME_SUFFIX}.log")


def _read_tail_text(path: Path, *, max_bytes: int) -> str:
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        start = max(0, size - max_bytes)
        handle.seek(start)
        data = handle.read()
    if start > 0:
        newline_index = data.find(b"\n")
        if newline_index >= 0:
            data = data[newline_index + 1 :]
    return data.decode("utf-8", errors="replace")


def _sanitize_terminal_tail(text: str, *, max_lines: int) -> str:
    """Retained helper for callers that prefer screen-first fallback behavior."""
    screen_lines = _render_terminal_screen(text)
    if screen_lines:
        visible = screen_lines[-max_lines:]
        return "\n".join(visible)
    return _sanitize_terminal_history(text, max_lines=max_lines)


def _mtime_iso_utc(path: Path) -> str:
    timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return timestamp.isoformat().replace("+00:00", "Z")


def _as_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
