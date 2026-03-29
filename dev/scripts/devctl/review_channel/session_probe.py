"""Session-detection helpers extracted from review_channel.core."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ACTIVE_SESSION_FRESHNESS_SECONDS = 120


@dataclass(frozen=True)
class ActiveSessionConflict:
    """One repo-visible session artifact that still looks live."""

    provider: str
    session_name: str
    metadata_path: str
    log_path: str | None
    age_seconds: int | None
    reason: str


def detect_active_session_conflicts(
    *,
    session_output_root: Path,
    freshness_seconds: int = ACTIVE_SESSION_FRESHNESS_SECONDS,
) -> tuple[ActiveSessionConflict, ...]:
    """Return live-looking session artifacts that should block a second launch."""
    session_dir = session_output_root / "sessions"
    if not session_dir.exists():
        return ()

    conflicts: list[ActiveSessionConflict] = []
    for provider in ("codex", "claude", "cursor"):
        metadata_path = session_dir / f"{provider}-conductor.json"
        if not metadata_path.exists():
            continue
        metadata = _load_session_metadata(metadata_path)
        if metadata is None:
            continue
        session_name = _session_metadata_text(metadata, "session_name") or f"{provider}-conductor"
        log_path_text = _session_metadata_text(metadata, "log_path")
        script_path_text = _session_metadata_text(metadata, "script_path")
        process_running = _probe_script_running(script_path_text)
        if process_running is True:
            conflicts.append(
                ActiveSessionConflict(
                    provider=provider,
                    session_name=session_name,
                    metadata_path=str(metadata_path),
                    log_path=log_path_text,
                    age_seconds=_log_age_seconds(log_path_text),
                    reason="existing conductor script process is still running",
                )
            )
            continue
        if process_running is False:
            continue
        age_seconds = _log_age_seconds(log_path_text)
        if age_seconds is None or age_seconds > freshness_seconds:
            continue
        conflicts.append(
            ActiveSessionConflict(
                provider=provider,
                session_name=session_name,
                metadata_path=str(metadata_path),
                log_path=log_path_text,
                age_seconds=age_seconds,
                reason=(
                    "session trace was updated "
                    f"{age_seconds}s ago and the script process could not be probed"
                ),
            )
        )
    return tuple(conflicts)


def summarize_active_session_conflicts(
    conflicts: tuple[ActiveSessionConflict, ...],
) -> str:
    """Render one concise duplicate-launch blocker message."""
    if not conflicts:
        return "none"
    parts: list[str] = []
    for conflict in conflicts:
        detail = f"{conflict.provider}: {conflict.reason}"
        if conflict.log_path:
            detail += f" (log: {conflict.log_path})"
        parts.append(detail)
    return "; ".join(parts)


def active_conductor_providers(
    *,
    session_output_root: Path,
    freshness_seconds: int = ACTIVE_SESSION_FRESHNESS_SECONDS,
) -> tuple[str, ...]:
    """Return provider ids with live-looking repo-owned conductor sessions."""
    conflicts = detect_active_session_conflicts(
        session_output_root=session_output_root,
        freshness_seconds=freshness_seconds,
    )
    return tuple(sorted({conflict.provider for conflict in conflicts}))


def _load_session_metadata(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _session_metadata_text(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _probe_script_running(script_path_text: str | None) -> bool | None:
    if not script_path_text or shutil.which("pgrep") is None:
        return None
    try:
        result = subprocess.run(
            ["pgrep", "-f", script_path_text],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 0 and result.stdout.strip():
        return True
    if result.returncode == 1:
        return False
    return None


def _log_age_seconds(log_path_text: str | None) -> int | None:
    if not log_path_text:
        return None
    log_path = Path(log_path_text)
    if not log_path.exists():
        return None
    modified = datetime.fromtimestamp(log_path.stat().st_mtime, tz=timezone.utc)
    age = datetime.now(tz=timezone.utc) - modified
    return max(0, int(age.total_seconds()))
