"""Session JSONL discovery helpers for ``rollout-tail``.

Both Codex and Claude Code write session traces on disk but use
different directory layouts and filename conventions. These helpers
isolate that layout knowledge so the parser and command-entry modules
stay provider-agnostic.
"""

from __future__ import annotations

from pathlib import Path

from .constants import (
    CLAUDE_PROJECTS_ROOT,
    CODEX_SESSIONS_ROOT,
    PROVIDER_CLAUDE,
    PROVIDER_CODEX,
)


def discover_latest_session(provider: str, *, root: Path | None = None) -> Path | None:
    """Return the newest session JSONL file for ``provider``.

    Auto-detection walks the provider's sessions tree and picks the
    single JSONL file with the most recent mtime. That matches how
    operators think about "the session I'm running right now" without
    needing to know the session UUID.
    """
    search_root = root if root is not None else _default_sessions_root(provider)
    if search_root is None or not search_root.exists():
        return None
    pattern = _session_glob(provider)
    candidates = [p for p in search_root.rglob(pattern) if p.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def resolve_session_file(
    provider: str,
    *,
    session_id: str | None,
    root: Path | None = None,
) -> Path | None:
    """Resolve a session JSONL path by id substring or newest mtime."""
    if session_id:
        search_root = root if root is not None else _default_sessions_root(provider)
        if search_root is None or not search_root.exists():
            return None
        matches = [
            p
            for p in search_root.rglob(_session_glob(provider))
            if session_id in p.name and p.is_file()
        ]
        if matches:
            return max(matches, key=lambda p: p.stat().st_mtime)
        return None
    return discover_latest_session(provider, root=root)


def session_id_from_path(path: Path, *, provider: str) -> str:
    """Derive a compact session identifier from the JSONL filename."""
    stem = path.stem
    if provider == PROVIDER_CODEX and stem.startswith("rollout-"):
        # rollout-<timestamp>-<uuid>; grab the trailing uuid portion.
        parts = stem.split("-")
        if len(parts) >= 6:
            return "-".join(parts[-5:])
        return stem
    return stem


def _default_sessions_root(provider: str) -> Path | None:
    if provider == PROVIDER_CODEX:
        return CODEX_SESSIONS_ROOT
    if provider == PROVIDER_CLAUDE:
        return CLAUDE_PROJECTS_ROOT
    return None


def _session_glob(provider: str) -> str:
    if provider == PROVIDER_CODEX:
        return "rollout-*.jsonl"
    if provider == PROVIDER_CLAUDE:
        return "*.jsonl"
    return "*.jsonl"
