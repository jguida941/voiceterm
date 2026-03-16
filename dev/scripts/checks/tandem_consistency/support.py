"""Shared helpers for tandem-consistency checks."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime


def current_utc() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


def skip_live_freshness() -> bool:
    """Skip live reviewer freshness on CI runners that cannot own the heartbeat."""
    return os.getenv("GITHUB_ACTIONS", "").strip().lower() == "true"


def extract_section(text: str, heading: str) -> str:
    """Extract a markdown section body by heading."""
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def extract_metadata_value(text: str, prefix: str) -> str:
    """Extract a list-style metadata value from the bridge markdown."""
    for line in text.splitlines():
        trimmed = line.strip().lstrip("-").strip()
        if trimmed.startswith(prefix):
            return trimmed[len(prefix) :].strip().strip("`").strip()
    return ""


def make_result(
    check: str,
    role: str,
    ok: bool,
    detail: str,
    **extra: object,
) -> dict[str, object]:
    """Build a standard tandem-consistency result payload."""
    payload = {
        "check": check,
        "role": role,
        "ok": ok,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def ack_references_instruction(instruction: str, ack: str, status: str) -> bool:
    """Check whether ACK or status text references the current instruction."""
    keywords = extract_instruction_keywords(instruction.lower())
    if not keywords:
        return True
    combined_lower = f"{ack}\n{status}".lower()
    matched = sum(1 for keyword in keywords if keyword in combined_lower)
    return matched >= min(2, len(keywords))


_KEYWORD_STOPWORDS = frozenset(
    {
        "the",
        "this",
        "that",
        "from",
        "into",
        "with",
        "after",
        "before",
        "should",
        "must",
        "keep",
        "does",
        "will",
        "when",
        "then",
        "also",
        "only",
        "still",
        "same",
    }
)

STALL_MARKERS = (
    "instruction unchanged",
    "continuing to poll",
    "waiting for codex review",
    "waiting for codex to review",
    "codex should review",
    "review and promote the next slice",
    "waiting for reviewer promotion",
)

REVIEWER_WAIT_STATE_MARKERS = (
    "hold steady",
    "waiting for reviewer promotion",
    "codex committing/pushing",
    "codex committing",
    "commit is in progress",
    "push in progress",
    "promotion pending",
)


def extract_instruction_keywords(instruction: str) -> list[str]:
    """Extract distinctive keywords from an instruction for tranche matching."""
    keywords: list[str] = []
    for token in re.findall(r"[a-z][a-z0-9_.-]{3,}", instruction):
        if token not in _KEYWORD_STOPWORDS:
            keywords.append(token)
            if len(keywords) >= 8:
                break
    return keywords


def leading_section_excerpt(text: str, *, max_lines: int = 12) -> str:
    """Return the leading non-empty lines from a section for current-state checks."""
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        lines.append(stripped)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)


def contains_any_marker(text: str, markers: tuple[str, ...]) -> bool:
    """Return True if any case-insensitive marker appears in the text."""
    lower = text.lower()
    return any(marker in lower for marker in markers)
