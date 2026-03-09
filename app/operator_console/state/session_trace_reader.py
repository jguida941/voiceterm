"""Read live review-channel session traces for the Operator Console."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SESSION_TRACE_DIR_CANDIDATES = (
    "dev/reports/review_channel/projections/latest/sessions",
    "dev/reports/review_channel/latest/sessions",
)
DEFAULT_SESSION_NAME_SUFFIX = "-conductor"
_ANSI_CSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_ANSI_OSC_RE = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)")


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


def load_live_session_trace(
    repo_root: Path,
    *,
    provider: str,
    review_full_path: Path | None = None,
    max_bytes: int = 24_000,
    max_lines: int = 120,
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
    tail_text = _sanitize_terminal_tail(
        _read_tail_text(log_path, max_bytes=max_bytes),
        max_lines=max_lines,
    )
    if not tail_text.strip():
        return None
    updated_at = _mtime_iso_utc(log_path)
    session_name = str(metadata.get("session_name") or f"{provider}{DEFAULT_SESSION_NAME_SUFFIX}")
    capture_mode = _as_text(metadata.get("capture_mode"))
    prepared_at = _as_text(metadata.get("prepared_at"))
    metadata_path = _as_text(metadata.get("_metadata_path"))
    return SessionTraceSnapshot(
        provider=provider,
        session_name=session_name,
        capture_mode=capture_mode,
        prepared_at=prepared_at,
        updated_at=updated_at,
        metadata_path=metadata_path,
        log_path=str(log_path),
        tail_text=tail_text,
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


def _resolve_log_path(
    *,
    metadata: dict[str, object],
    provider: str,
) -> Path | None:
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
        handle.seek(max(0, size - max_bytes))
        return handle.read().decode("utf-8", errors="replace")


def _sanitize_terminal_tail(text: str, *, max_lines: int) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _ANSI_OSC_RE.sub("", text)
    text = _ANSI_CSI_RE.sub("", text)
    text = _apply_backspaces(text)
    lines = []
    for raw_line in text.splitlines():
        line = _strip_controls(raw_line)
        if not line.strip():
            continue
        if line.startswith("Script started on ") or line.startswith("Script done on "):
            continue
        lines.append(line)
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    return "\n".join(lines)


def _apply_backspaces(text: str) -> str:
    buffer: list[str] = []
    for char in text:
        if char == "\b":
            if buffer:
                buffer.pop()
            continue
        buffer.append(char)
    return "".join(buffer)


def _strip_controls(text: str) -> str:
    return "".join(
        char
        for char in text
        if char == "\t" or 32 <= ord(char) or ord(char) >= 160
    )


def _mtime_iso_utc(path: Path) -> str:
    timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return timestamp.isoformat().replace("+00:00", "Z")


def _as_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
