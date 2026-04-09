"""Command entrypoint for ``devctl agent-mind``.

Thin orchestrator over the rollout-tail parser and the agent-mind
slice builder: resolve the latest session JSONL for the requested
provider, parse the recent events, promote them to a typed
:class:`AgentMindSlice`, and dispatch to the renderer + optional
projection writer. Heavy lifting lives in sibling modules so this
file stays at an obvious level of abstraction.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ..rollout_tail.discovery import discover_latest_session, session_id_from_path
from ..rollout_tail.parser import parse_rollout_file
from .projection import write_projection
from .renderers import render_json, render_markdown, render_terminal
from .slice_builder import SliceRequest, build_slice

SUPPORTED_AGENTS: tuple[str, ...] = ("codex", "claude")

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
        since_cursor=_normalize_cursor(getattr(args, "since_cursor", None)),
    )
    _emit(args, slice_=slice_)
    if bool(getattr(args, "project", False)):
        _write_projection_or_warn(slice_)
    return 0


def _normalize_provider(args: Any) -> str | None:
    provider = str(getattr(args, "agent", "") or "").strip().lower()
    if provider not in SUPPORTED_AGENTS:
        print(
            f"error: --agent must be one of {', '.join(SUPPORTED_AGENTS)}",
            file=sys.stderr,
        )
        return None
    return provider


def _resolve_session_path(provider: str, args: Any) -> Path | None:
    root_override = getattr(args, "sessions_root", None)
    root = Path(root_override).expanduser() if root_override else None
    return discover_latest_session(provider, root=root)


def _normalize_limit(raw_limit: Any) -> int:
    try:
        value = int(raw_limit)
    except (TypeError, ValueError):
        return _DEFAULT_LIMIT
    return value if value > 0 else _DEFAULT_LIMIT


def _normalize_cursor(raw: Any) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _build_slice_from_session(
    session_path: Path,
    *,
    provider: str,
    limit: int,
    since_cursor: str | None,
):
    events = parse_rollout_file(
        session_path,
        provider=provider,
        limit=_PARSER_TAIL_LIMIT,
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
