"""Command entrypoint for ``devctl rollout-tail``.

Thin orchestrator that resolves the target session JSONL, parses the
most recent events through the typed contract, and dispatches to the
requested render format. Session discovery and per-line classification
live in sibling modules so this file stays small and obvious.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .constants import SUPPORTED_PROVIDERS
from .discovery import resolve_session_file
from .parser import parse_rollout_file
from .renderers import render_json, render_markdown, render_terminal


def run(args) -> int:
    """Entry point invoked by ``devctl.py rollout-tail``."""
    provider = str(getattr(args, "provider", "")).strip()
    if provider not in SUPPORTED_PROVIDERS:
        print(
            f"error: --provider must be one of {', '.join(SUPPORTED_PROVIDERS)}",
            file=sys.stderr,
        )
        return 2

    session_path = _resolve_session(args, provider=provider)
    if session_path is None:
        session_id = getattr(args, "session_id", None) or "auto"
        print(
            f"error: no {provider} session JSONL found (session_id={session_id})",
            file=sys.stderr,
        )
        return 1

    limit = max(1, int(getattr(args, "limit", 50) or 50))
    events = parse_rollout_file(session_path, provider=provider, limit=limit)

    _emit(args, events=events, source=session_path)
    _warn_follow_unsupported(args)
    return 0


def _resolve_session(args, *, provider: str) -> Path | None:
    session_id = getattr(args, "session_id", None)
    root_override = getattr(args, "sessions_root", None)
    root = Path(root_override).expanduser() if root_override else None
    return resolve_session_file(provider, session_id=session_id, root=root)


def _emit(args, *, events, source: Path) -> None:
    fmt = str(getattr(args, "format", "md") or "md")
    if fmt == "json":
        print(render_json(events, source=source))
        return
    if fmt == "terminal":
        print(render_terminal(events, source=source))
        return
    print(render_markdown(events, source=source))


def _warn_follow_unsupported(args) -> None:
    if bool(getattr(args, "follow", False)):
        print(
            "[rollout-tail] --follow is not yet implemented; printed snapshot only.",
            file=sys.stderr,
        )
