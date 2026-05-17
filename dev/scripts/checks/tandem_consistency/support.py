"""Shared helpers for tandem-consistency checks."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone

from dev.scripts.devctl.review_channel.peer_liveness import (
    IMPLEMENTER_STALL_MARKERS,
    REVIEWER_WAIT_STATE_MARKERS,
)
from dev.scripts.devctl.review_channel.bridge_heading_aliases import bridge_heading_aliases


def current_utc() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def skip_live_freshness() -> bool:
    """Skip live reviewer freshness on CI runners that cannot own the heartbeat."""
    return os.getenv("GITHUB_ACTIONS", "").strip().lower() == "true"


def extract_section(text: str, heading: str) -> str:
    """Extract a markdown section body by canonical heading or legacy alias."""
    for candidate in bridge_heading_aliases(heading):
        pattern = re.compile(
            rf"^## {re.escape(candidate)}\s*$\n(.*?)(?=^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return ""


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


STALL_MARKERS = IMPLEMENTER_STALL_MARKERS


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
