"""Acceptance semantics for reviewer-owned bridge sections."""

from __future__ import annotations

import re

from .handoff_constants import MARKDOWN_ITEM_RE

_ACCEPTED_VERDICT_PREFIX_RE = re.compile(
    r"^(?:reviewer[- ]accepted|accepted|all\s+green|resolved)\b",
    re.IGNORECASE,
)
_CLEAR_FINDINGS_PREFIX_RE = re.compile(
    r"^(?:\(none\)|none|no\s+blockers|all\s+clear|all\s+green|resolved)\b",
    re.IGNORECASE,
)


def _normalized_bridge_lines(text: str) -> tuple[str, ...]:
    """Return non-empty bridge lines normalized for section-state checks."""
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = MARKDOWN_ITEM_RE.match(stripped)
        candidate = match.group("value").strip() if match is not None else stripped
        if candidate:
            lines.append(candidate.lower())
    return tuple(lines)


def bridge_review_accepted(snapshot) -> bool:
    """Return True only when reviewer-owned bridge sections show acceptance."""
    verdict_lines = _normalized_bridge_lines(
        snapshot.sections.get("Current Verdict", "")
    )
    if not verdict_lines:
        return False
    if _ACCEPTED_VERDICT_PREFIX_RE.match(verdict_lines[0]) is None:
        return False

    finding_lines = _normalized_bridge_lines(
        snapshot.sections.get("Open Findings", "")
    )
    return not finding_lines or all(
        _CLEAR_FINDINGS_PREFIX_RE.match(line) is not None
        for line in finding_lines
    )
