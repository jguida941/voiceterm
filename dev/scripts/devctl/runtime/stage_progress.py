"""Typed progress events for long-running devctl stages."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
from typing import Any
from uuid import uuid4

from ..config import REPO_ROOT

DEFAULT_PROGRESS_ROOT_REL = "dev/reports/progress"
PROGRESS_ROOT_ENV = "DEVCTL_PROGRESS_ROOT"
ARTIFACT_WRITES_ENV = "DEVCTL_NO_ARTIFACT_WRITES"
PROGRESS_DISABLE_ENV = "DEVCTL_PROGRESS_DISABLE"

_WRITE_LOCK = threading.Lock()


@dataclass(frozen=True)
class StageProgressEvent:
    """Durable event describing a devctl stage transition or heartbeat."""

    event_id: str
    timestamp_utc: str
    command_name: str
    phase: str
    status: str
    detail: str = ""
    elapsed_seconds: float = 0.0
    pid: int = 0
    child_pid: int | None = None
    command: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["command"] = list(self.command)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "StageProgressEvent":
        command = payload.get("command") or ()
        if not isinstance(command, (list, tuple)):
            command = ()
        return cls(
            event_id=str(payload.get("event_id") or ""),
            timestamp_utc=str(payload.get("timestamp_utc") or ""),
            command_name=str(payload.get("command_name") or ""),
            phase=str(payload.get("phase") or ""),
            status=str(payload.get("status") or ""),
            detail=str(payload.get("detail") or ""),
            elapsed_seconds=float(payload.get("elapsed_seconds") or 0.0),
            pid=int(payload.get("pid") or 0),
            child_pid=_optional_int(payload.get("child_pid")),
            command=tuple(str(part) for part in command),
        )


@dataclass(frozen=True)
class StageProgressContext:
    """Optional child-command context attached to a progress event."""

    child_pid: int | None = None
    command: tuple[str, ...] = ()


def build_stage_progress_event(
    *,
    command_name: str,
    phase: str,
    status: str,
    detail: str = "",
    elapsed_seconds: float = 0.0,
    context: StageProgressContext | None = None,
) -> StageProgressEvent:
    """Build one progress event with normalized fields."""
    resolved_context = context or StageProgressContext()
    return StageProgressEvent(
        event_id=f"stage_progress:{uuid4().hex}",
        timestamp_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        command_name=str(command_name or "").strip() or "unknown",
        phase=str(phase or "").strip() or "unknown",
        status=str(status or "").strip() or "running",
        detail=" ".join(str(detail or "").split()),
        elapsed_seconds=round(max(0.0, float(elapsed_seconds or 0.0)), 2),
        pid=os.getpid(),
        child_pid=resolved_context.child_pid,
        command=tuple(str(part) for part in resolved_context.command),
    )


def record_stage_progress_event(
    event: StageProgressEvent,
    *,
    repo_root: Path = REPO_ROOT,
) -> bool:
    """Append an event and refresh the latest snapshot when writes are allowed."""
    if progress_writes_suppressed():
        return False
    progress_root = resolve_progress_root(repo_root=repo_root)
    payload = event.to_dict()
    encoded = json.dumps(payload, sort_keys=True)
    with _WRITE_LOCK:
        progress_root.mkdir(parents=True, exist_ok=True)
        with (progress_root / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(encoded + "\n")
        _write_json_atomic(progress_root / "latest.json", payload)
    return True


def read_progress_snapshot(
    *,
    repo_root: Path = REPO_ROOT,
    limit: int = 10,
) -> dict[str, Any]:
    """Read the latest progress event plus a bounded recent event tail."""
    progress_root = resolve_progress_root(repo_root=repo_root)
    latest = _read_json_object(progress_root / "latest.json")
    recent = read_progress_events(repo_root=repo_root, limit=limit)
    return {
        "progress_root": str(progress_root),
        "latest": latest,
        "recent": [event.to_dict() for event in recent],
    }


def read_progress_events(
    *,
    repo_root: Path = REPO_ROOT,
    limit: int = 10,
) -> tuple[StageProgressEvent, ...]:
    """Return the newest progress events from the JSONL log."""
    path = resolve_progress_root(repo_root=repo_root) / "events.jsonl"
    if not path.exists():
        return ()
    max_rows = max(0, int(limit or 0))
    rows: deque[StageProgressEvent] = deque(maxlen=max_rows or 1)
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = _parse_json_object(line)
                if payload is None:
                    continue
                rows.append(StageProgressEvent.from_dict(payload))
    except OSError:
        return ()
    if max_rows <= 0:
        return ()
    return tuple(rows)


def resolve_progress_root(*, repo_root: Path = REPO_ROOT) -> Path:
    """Resolve the progress artifact root, supporting test/runtime override."""
    raw = os.environ.get(PROGRESS_ROOT_ENV, "").strip()
    if raw:
        path = Path(raw).expanduser()
        return path if path.is_absolute() else repo_root / path
    return repo_root / DEFAULT_PROGRESS_ROOT_REL


def progress_writes_suppressed() -> bool:
    """Return true when progress artifact writes must not occur."""
    return (
        os.environ.get(ARTIFACT_WRITES_ENV, "") == "1"
        or os.environ.get(PROGRESS_DISABLE_ENV, "") == "1"
    )


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return _parse_json_object(text)


def _parse_json_object(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "ARTIFACT_WRITES_ENV",
    "DEFAULT_PROGRESS_ROOT_REL",
    "PROGRESS_DISABLE_ENV",
    "PROGRESS_ROOT_ENV",
    "StageProgressContext",
    "StageProgressEvent",
    "build_stage_progress_event",
    "progress_writes_suppressed",
    "read_progress_events",
    "read_progress_snapshot",
    "record_stage_progress_event",
    "resolve_progress_root",
]
