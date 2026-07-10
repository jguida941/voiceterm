"""Command entrypoint for ``devctl agent-mind``.

Thin orchestrator over the rollout-tail parser and the agent-mind
slice builder: resolve the latest session JSONL for the requested
provider, parse the recent events, promote them to a typed
:class:`AgentMindSlice`, and dispatch to the renderer + optional
projection writer. Heavy lifting lives in sibling modules so this
file stays at an obvious level of abstraction.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...runtime.provider_registry import (
    KNOWN_AGENT_PROVIDERS,
    is_valid_provider_id,
    normalize_provider_id,
    provider_id_error,
)
from ..rollout_tail.discovery import resolve_session_file, session_id_from_path
from ..rollout_tail.parser import parse_rollout_file
from .projection import resolve_projection_path, write_projection
from .renderers import render_json, render_markdown, render_terminal
from .slice_builder import SliceRequest, build_slice

SUPPORTED_AGENTS: tuple[str, ...] = KNOWN_AGENT_PROVIDERS
_PERSISTED_CURSOR_TOKEN = "last_projection"

_DEFAULT_LIMIT = 20
# Parser tail window: we fetch a wider slice than the user's --limit so
# the decision-event filter has room to drop noise before we truncate.
_PARSER_TAIL_LIMIT = 400


def run(args: Any) -> int:
    """Entry point invoked by ``devctl.py agent-mind``."""
    provider = _normalize_provider(args)
    if provider is None:
        return 2
    session_path = _resolve_session_path(provider, args)
    if session_path is None:
        print(
            f"error: no {provider} session JSONL found",
            file=sys.stderr,
        )
        return 1
    limit = _normalize_limit(getattr(args, "limit", _DEFAULT_LIMIT))
    slice_ = _build_slice_from_session(
        session_path,
        provider=provider,
        limit=limit,
        since_cursor=_normalize_cursor(
            getattr(args, "since_cursor", None),
            provider=provider,
        ),
    )
    _emit(args, slice_=slice_)
    if bool(getattr(args, "project", False)):
        _write_projection_or_warn(slice_)
    return 0


def _normalize_provider(args: Any) -> str | None:
    provider = normalize_provider_id(getattr(args, "agent", ""))
    if not is_valid_provider_id(provider):
        print(provider_id_error("--agent"), file=sys.stderr)
        return None
    return provider


def _resolve_session_path(provider: str, args: Any) -> Path | None:
    root_override = getattr(args, "sessions_root", None)
    root = Path(root_override).expanduser() if root_override else None
    return resolve_session_file(
        provider,
        session_id=getattr(args, "session_id", None),
        exclude_session_ids=_excluded_session_ids(provider, args),
        root=root,
    )


def _excluded_session_ids(provider: str, args: Any) -> tuple[str, ...]:
    explicit = tuple(
        text
        for text in (
            str(value or "").strip()
            for value in getattr(args, "exclude_session_id", None) or ()
        )
        if text
    )
    caller_agent = normalize_provider_id(os.environ.get("DEVCTL_CALLER_AGENT", ""))
    if caller_agent != provider:
        return explicit
    caller_session_id = str(os.environ.get("DEVCTL_CALLER_SESSION_ID", "")).strip()
    if not caller_session_id:
        return explicit
    return (*explicit, caller_session_id)


def _normalize_limit(raw_limit: Any) -> int:
    try:
        value = int(raw_limit)
    except (TypeError, ValueError):
        return _DEFAULT_LIMIT
    return value if value > 0 else _DEFAULT_LIMIT


def _normalize_cursor(raw: Any, *, provider: str) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if text == _PERSISTED_CURSOR_TOKEN:
        return _persisted_cursor(provider)
    return text or None


def _persisted_cursor(provider: str) -> str | None:
    path = resolve_projection_path(provider, repo_root=Path(REPO_ROOT))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    cursor = str(payload.get("last_cursor") or "").strip()
    return cursor or None


def _build_slice_from_session(
    session_path: Path,
    *,
    provider: str,
    limit: int,
    since_cursor: str | None,
):
    # When cursor-based polling is active, read the entire file so the
    # cursor filter sees every event regardless of how many noise lines
    # intervene.  Without a cursor the fixed tail window keeps the
    # common-case fast and memory-bounded.
    parser_limit: int | None = None if since_cursor else _PARSER_TAIL_LIMIT
    events = parse_rollout_file(
        session_path,
        provider=provider,
        limit=parser_limit,
    )
    request = SliceRequest(
        agent_provider=provider,
        session_id=session_id_from_path(session_path, provider=provider),
        session_path=session_path,
        since_cursor=since_cursor,
        limit=limit,
    )
    return build_slice(events, request)


def _emit(args: Any, *, slice_) -> None:
    fmt = str(getattr(args, "format", "md") or "md").lower()
    if fmt == "json":
        print(render_json(slice_))
        return
    if fmt == "terminal":
        print(render_terminal(slice_))
        return
    print(render_markdown(slice_))


def _write_projection_or_warn(slice_) -> None:
    """Persist the projection file, surfacing write errors as stderr warnings.

    We swallow ``OSError`` here and keep the command exit code at 0 so a
    missing reports directory on a read-only mount does not blow up the
    happy path: the stdout render still succeeds, and the operator sees
    a repo-local warning about the projection failure.
    """
    try:
        target = write_projection(slice_, repo_root=Path(REPO_ROOT))
    except OSError as exc:
        print(f"warning: agent-mind projection write failed: {exc}", file=sys.stderr)
        return
    print(f"[agent-mind] projection written: {target}", file=sys.stderr)


__all__ = [
    "SUPPORTED_AGENTS",
    "run",
]
