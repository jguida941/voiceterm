"""Shared text-cleanup helpers for bridge-compatible markdown sections."""

from __future__ import annotations

import re

ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
TRANSCRIPT_LINE_PATTERNS = (
    re.compile(r"(?i)^test .+\.\.\. ok$"),
    re.compile(r"(?i)^running \d+ tests$"),
    re.compile(r"(?i)^test result:"),
    re.compile(r"(?i)^compiling "),
    re.compile(r"(?i)^finished "),
    re.compile(r"(?i)^doc-tests "),
    re.compile(r"(?i)^\s*running tests/"),
    re.compile(r"(?i)^\[process-sweep-post\]"),
    re.compile(r"(?i)^last login:"),
    re.compile(r"(?i)^/bin/zsh "),
    re.compile(r"(?i)^❯ "),
    re.compile(r"(?i)^⏺ "),
)


def has_ansi_escape(text: str) -> bool:
    return ANSI_ESCAPE_RE.search(text) is not None


def has_control_chars(text: str) -> bool:
    return CONTROL_CHAR_RE.search(text) is not None


def is_transcript_line(line: str) -> bool:
    """Return True when a stripped line matches known transcript/test output."""
    if not line:
        return False
    return any(pattern.search(line) for pattern in TRANSCRIPT_LINE_PATTERNS)


def collapse_blank_lines(lines: list[str]) -> list[str]:
    """Collapse consecutive blank lines into a single blank line."""
    collapsed: list[str] = []
    previous_blank = False
    for raw in lines:
        blank = not raw.strip()
        if blank and previous_blank:
            continue
        collapsed.append(raw)
        previous_blank = blank
    return collapsed


def strip_terminal_bytes(text: str) -> str:
    """Remove ANSI escapes and raw control characters from text."""
    without_ansi = ANSI_ESCAPE_RE.sub("", text)
    return CONTROL_CHAR_RE.sub("", without_ansi)


def strip_transcript_lines(text: str) -> str:
    kept = [
        line.rstrip()
        for line in text.splitlines()
        if not is_transcript_line(line.strip())
    ]
    return "\n".join(collapse_blank_lines(kept)).strip()


def find_transcript_lines(text: str) -> list[str]:
    hits: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or not is_transcript_line(line):
            continue
        if line not in hits:
            hits.append(line)
    return hits
