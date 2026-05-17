"""Shared constants for the ``rollout-tail`` command.

Keeping provider identifiers and default sessions roots in one module
lets each rollout-tail helper file import them without pulling in the
larger parser/renderer graph.
"""

from __future__ import annotations

from pathlib import Path


CODEX_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"
CLAUDE_PROJECTS_ROOT = Path.home() / ".claude" / "projects"

PROVIDER_CODEX = "codex"
PROVIDER_CLAUDE = "claude"

SUPPORTED_PROVIDERS: tuple[str, ...] = (PROVIDER_CODEX, PROVIDER_CLAUDE)
