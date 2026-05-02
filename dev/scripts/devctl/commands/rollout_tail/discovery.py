"""Session JSONL discovery helpers for ``rollout-tail``.

Both Codex and Claude Code write session traces on disk but use
different directory layouts and filename conventions. These helpers
isolate that layout knowledge so the parser and command-entry modules
stay provider-agnostic.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .constants import (
    CLAUDE_PROJECTS_ROOT,
    CODEX_SESSIONS_ROOT,
    PROVIDER_CLAUDE,
    PROVIDER_CODEX,
)

# Claude session files live at ``<projects>/<project>/<uuid>.jsonl`` (depth 2).
# Subagent traces under ``<project>/<uuid>/subagents/*.jsonl`` must be ignored
# so the newest real session is picked even when a subagent writes later.
_CLAUDE_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)


def discover_latest_session(
    provider: str,
    *,
    root: Path | None = None,
    exclude_session_ids: Iterable[str] | None = None,
) -> Path | None:
    """Return the newest session JSONL file for ``provider``.

    Auto-detection walks the provider's sessions tree and picks the
    single JSONL file with the most recent mtime. That matches how
    operators think about "the session I'm running right now" without
    needing to know the session UUID.
    """
    search_root = root if root is not None else default_sessions_root(provider)
    if search_root is None or not search_root.exists():
        return None
    candidates = [
        p
        for p in _iter_session_files(provider, search_root)
        if p.is_file()
        and not _matches_any_session_identifier(
            p,
            provider=provider,
            identifiers=exclude_session_ids,
        )
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def resolve_session_file(
    provider: str,
    *,
    session_id: str | None,
    exclude_session_ids: Iterable[str] | None = None,
    root: Path | None = None,
) -> Path | None:
    """Resolve a session JSONL path by id substring or newest mtime."""
    if session_id:
        search_root = root if root is not None else default_sessions_root(provider)
        if search_root is None or not search_root.exists():
            return None
        matches = [
            p
            for p in _iter_session_files(provider, search_root)
            if _matches_session_identifier(p, provider=provider, identifier=session_id)
            and p.is_file()
            and not _matches_any_session_identifier(
                p,
                provider=provider,
                identifiers=exclude_session_ids,
            )
        ]
        if matches:
            return max(matches, key=lambda p: p.stat().st_mtime)
        return None
    return discover_latest_session(
        provider,
        root=root,
        exclude_session_ids=exclude_session_ids,
    )


def _matches_any_session_identifier(
    path: Path,
    *,
    provider: str,
    identifiers: Iterable[str] | None,
) -> bool:
    return any(
        _matches_session_identifier(path, provider=provider, identifier=identifier)
        for identifier in identifiers or ()
    )


def _matches_session_identifier(path: Path, *, provider: str, identifier: str) -> bool:
    text = str(identifier or "").strip()
    if not text:
        return False
    session_id = session_id_from_path(path, provider=provider)
    return (
        text == session_id
        or text in session_id
        or text in path.name
        or text in str(path)
    )


def iter_session_files(provider: str, search_root: Path) -> Iterable[Path]:
    """Yield candidate session JSONL files for ``provider`` under ``search_root``.

    Codex writes to ``sessions/YYYY/MM/DD/rollout-*.jsonl``, so a full
    recursive walk for ``rollout-*.jsonl`` is correct. Claude instead
    writes ``<project>/<uuid>.jsonl`` at exactly depth 2 and may also
    write subagent traces several levels deeper; a narrow glob plus a
    UUID-shape filter keeps the picker on real session files.

    Public iterator used by ``rollout-tail`` newest-mtime discovery and by
    ``agent_work_board`` multi-session enumeration. Subagent traces are
    intentionally excluded — see ``iter_claude_subagent_files`` for those.
    """
    if provider == PROVIDER_CODEX:
        yield from search_root.rglob("rollout-*.jsonl")
        return
    if provider == PROVIDER_CLAUDE:
        for candidate in search_root.glob("*/*.jsonl"):
            if _CLAUDE_UUID_RE.fullmatch(candidate.stem):
                yield candidate
        return
    yield from search_root.rglob("*.jsonl")


# Back-compat alias kept for any existing internal caller; new code should
# import the public name above.
_iter_session_files = iter_session_files


def iter_claude_subagent_files(search_root: Path) -> Iterable[Path]:
    """Yield Claude Code Task-tool subagent trace files.

    Claude writes subagent traces under ``<project>/<parent_uuid>/subagents/*.jsonl``.
    These are deliberately excluded from ``iter_session_files`` because the
    rollout-tail picker wants the newest real session, not a subagent that
    may have written later. The work-board projection (``agent_work_board``)
    needs them so it can show every operator-used delegated agent.

    Yields tuples are NOT used here for simplicity; callers can derive the
    parent session UUID from ``path.parent.parent.name`` (the directory two
    levels up from the file is the parent session UUID).
    """
    for candidate in search_root.glob("*/*/subagents/*.jsonl"):
        if candidate.is_file():
            yield candidate


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


def default_sessions_root(provider: str) -> Path | None:
    """Return the provider's default local session root, when known."""
    if provider == PROVIDER_CODEX:
        return CODEX_SESSIONS_ROOT
    if provider == PROVIDER_CLAUDE:
        return CLAUDE_PROJECTS_ROOT
    return None


_default_sessions_root = default_sessions_root
