"""Public surface for the ``rollout-tail`` devctl command.

Re-exports the small set of entry-point helpers consumed by ``cli.py``,
the CLI parser module, and the test suite. Implementation is split
across sibling modules in this package to keep each file under the
code-shape soft limit and cleanly separated by concern.
"""

from __future__ import annotations

from .command import run
from .constants import (
    CLAUDE_PROJECTS_ROOT,
    CODEX_SESSIONS_ROOT,
    PROVIDER_CLAUDE,
    PROVIDER_CODEX,
    SUPPORTED_PROVIDERS,
)
from .discovery import discover_latest_session, resolve_session_file
from .parser import classify_event, parse_rollout_file
from .renderers import render_json, render_markdown, render_terminal

__all__ = [
    "CLAUDE_PROJECTS_ROOT",
    "CODEX_SESSIONS_ROOT",
    "PROVIDER_CLAUDE",
    "PROVIDER_CODEX",
    "SUPPORTED_PROVIDERS",
    "classify_event",
    "discover_latest_session",
    "parse_rollout_file",
    "render_json",
    "render_markdown",
    "render_terminal",
    "resolve_session_file",
    "run",
]
