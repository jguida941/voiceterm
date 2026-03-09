"""Markdown bridge parsing helpers for the Operator Console."""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_BRIDGE_REL = "code_audit.md"
SECTION_RE = re.compile(r"^##\s+(?P<name>.+?)\s*$")
MODE_RE = re.compile(r"^- Mode:\s*(?P<value>.+?)\s*$")
LAST_CODEX_POLL_RE = re.compile(r"^- Last Codex poll:\s*`(?P<value>.+?)`\s*$")
LAST_WORKTREE_HASH_RE = re.compile(
    r"^- Last non-audit worktree hash:\s*`(?P<value>.+?)`\s*$"
)


@dataclass(frozen=True)
class BridgeMetadata:
    """Top-level metadata parsed from `code_audit.md`."""

    review_mode: str | None
    last_codex_poll: str | None
    last_worktree_hash: str | None


def parse_markdown_sections(markdown_text: str) -> dict[str, str]:
    """Parse second-level markdown sections into a name-to-body map."""
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []
    for raw_line in markdown_text.splitlines():
        match = SECTION_RE.match(raw_line.strip())
        if match is not None:
            _flush_section(sections, current_name, current_lines)
            current_name = match.group("name").strip()
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(raw_line.rstrip())
    _flush_section(sections, current_name, current_lines)
    return sections


def extract_bridge_metadata(markdown_text: str) -> BridgeMetadata:
    """Extract the current bridge-mode metadata block."""
    return BridgeMetadata(
        review_mode=_match_metadata(MODE_RE, markdown_text),
        last_codex_poll=_match_metadata(LAST_CODEX_POLL_RE, markdown_text),
        last_worktree_hash=_match_metadata(LAST_WORKTREE_HASH_RE, markdown_text),
    )


def _flush_section(
    sections: dict[str, str],
    current_name: str | None,
    current_lines: list[str],
) -> None:
    if current_name is None:
        return
    sections[current_name] = "\n".join(current_lines).strip()


def _match_metadata(pattern: re.Pattern[str], markdown_text: str) -> str | None:
    for raw_line in markdown_text.splitlines():
        match = pattern.match(raw_line.strip())
        if match is not None:
            return match.group("value").strip()
    return None
