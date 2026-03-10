"""Shared markdown section parser used by both the operator console and devctl."""

from __future__ import annotations

import re

SECTION_HEADING_RE = re.compile(r"^##\s+(?P<name>.+?)\s*$")


def parse_markdown_sections(markdown_text: str) -> dict[str, str]:
    """Parse second-level markdown sections into a heading-name to body map."""
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []
    for raw_line in markdown_text.splitlines():
        match = SECTION_HEADING_RE.match(raw_line.strip())
        if match is not None:
            _flush_section(sections, current_name, current_lines)
            current_name = match.group("name").strip()
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(raw_line.rstrip())
    _flush_section(sections, current_name, current_lines)
    return sections


def _flush_section(
    sections: dict[str, str],
    current_name: str | None,
    current_lines: list[str],
) -> None:
    if current_name is None:
        return
    sections[current_name] = "\n".join(current_lines).strip()
