"""Provider session discovery diagnostics for `/develop`."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from ..rollout_tail.constants import (
    PROVIDER_CLAUDE,
    PROVIDER_CODEX,
)
from ..rollout_tail.discovery import (
    default_sessions_root,
    iter_session_files,
    session_id_from_path,
)
from .models import DevelopmentSessionDiscoveryRow

_MAX_CANDIDATES_PER_PROVIDER = 40
_MAX_ROWS = 8
_PROVIDERS = (PROVIDER_CODEX, PROVIDER_CLAUDE)


def discover_sessions_for_runtime(
    *,
    repo_root: Path,
    registered_sessions: set[tuple[str, str]],
) -> tuple[DevelopmentSessionDiscoveryRow, ...]:
    """Return recent repo session files, marking work-board registration gaps."""
    rows: list[DevelopmentSessionDiscoveryRow] = []
    for provider in _PROVIDERS:
        rows.extend(
            _provider_rows(
                provider=provider,
                repo_root=repo_root,
                registered_sessions=registered_sessions,
            )
        )
    rows.sort(key=lambda row: (row.registered, row.age_seconds, row.provider))
    return tuple(rows[:_MAX_ROWS])


def _provider_rows(
    *,
    provider: str,
    repo_root: Path,
    registered_sessions: set[tuple[str, str]],
) -> tuple[DevelopmentSessionDiscoveryRow, ...]:
    root = _session_root(provider)
    if root is None or not root.exists():
        return ()
    rows: list[DevelopmentSessionDiscoveryRow] = []
    for path in _recent_session_files(provider, root):
        if _session_cwd(path) != str(repo_root):
            continue
        session_id = session_id_from_path(path, provider=provider)
        registered = (provider, session_id) in registered_sessions
        rows.append(
            DevelopmentSessionDiscoveryRow(
                provider=provider,
                session_id=session_id,
                registered=registered,
                age_seconds=_age_seconds(path),
                source_path=str(path),
            )
        )
    return tuple(rows)


def _recent_session_files(provider: str, root: Path) -> tuple[Path, ...]:
    candidates = [path for path in iter_session_files(provider, root) if path.is_file()]
    candidates.sort(key=lambda path: _mtime(path), reverse=True)
    return tuple(candidates[:_MAX_CANDIDATES_PER_PROVIDER])


def _session_cwd(path: Path) -> str:
    try:
        handle = path.open("r", encoding="utf-8")
    except OSError:
        return ""
    with handle:
        for _index, line in zip(range(20), handle):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            cwd = _cwd_from_payload(payload)
            if cwd:
                return cwd
    return ""


def _cwd_from_payload(payload: object) -> str:
    if not isinstance(payload, Mapping):
        return ""
    cwd = _text(payload.get("cwd"))
    if cwd:
        return cwd
    nested = payload.get("payload")
    if isinstance(nested, Mapping):
        return _text(nested.get("cwd"))
    return ""


def _session_root(provider: str) -> Path | None:
    return default_sessions_root(provider)


def _age_seconds(path: Path) -> int:
    return max(int((datetime.now(timezone.utc).timestamp() - _mtime(path))), 0)


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["discover_sessions_for_runtime"]
