"""Validation helpers for flat live-state bridge section bodies."""

from __future__ import annotations

import re

MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")


def find_embedded_markdown_headings(text: str | None) -> tuple[str, ...]:
    """Return markdown heading lines that are invalid inside flat bridge sections."""
    if not text:
        return ()
    hits: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or not MARKDOWN_HEADING_RE.match(stripped):
            continue
        if stripped not in hits:
            hits.append(stripped)
    return tuple(hits)
