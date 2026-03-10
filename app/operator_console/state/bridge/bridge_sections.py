"""Markdown bridge parsing helpers for the Operator Console bridge package."""

from __future__ import annotations

import re
from dataclasses import dataclass

from dev.scripts.devctl.markdown_sections import parse_markdown_sections

DEFAULT_BRIDGE_REL = "code_audit.md"
MODE_RE = re.compile(r"^- Mode:\s*(?P<value>.+?)\s*$")
LAST_CODEX_POLL_RE = re.compile(r"^- Last Codex poll:\s*`(?P<value>.+?)`\s*$")
LAST_WORKTREE_HASH_RE = re.compile(
    r"^- Last non-audit worktree hash:\s*`(?P<value>.+?)`\s*$"
)

# Re-export so callers that import from this module keep working.
parse_markdown_sections = parse_markdown_sections


@dataclass(frozen=True)
class BridgeMetadata:
    """Top-level metadata parsed from `code_audit.md`."""

    review_mode: str | None
    last_codex_poll: str | None
    last_worktree_hash: str | None


def extract_bridge_metadata(markdown_text: str) -> BridgeMetadata:
    """Extract the current bridge-mode metadata block."""
    return BridgeMetadata(
        review_mode=_match_metadata(MODE_RE, markdown_text),
        last_codex_poll=_match_metadata(LAST_CODEX_POLL_RE, markdown_text),
        last_worktree_hash=_match_metadata(LAST_WORKTREE_HASH_RE, markdown_text),
    )


def _match_metadata(pattern: re.Pattern[str], markdown_text: str) -> str | None:
    for raw_line in markdown_text.splitlines():
        match = pattern.match(raw_line.strip())
        if match is not None:
            return match.group("value").strip()
    return None
