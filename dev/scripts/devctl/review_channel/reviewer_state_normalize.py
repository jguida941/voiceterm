"""Instruction and findings normalization helpers for reviewer state writes."""

from __future__ import annotations

import hashlib
import re

from .handoff import extract_bridge_snapshot, summarize_bridge_liveness

SECTION_RE_TEMPLATE = r"^(## {heading}\s*\n)(.*?)(?=^## |\Z)"
_OPEN_FINDINGS_HEADING = "Open Findings"


def current_instruction_body_from_bridge_text(bridge_text: str) -> str:
    match = re.search(
        SECTION_RE_TEMPLATE.format(
            heading=re.escape("Current Instruction For Implementer"),
        ),
        bridge_text,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        return ""
    return normalize_instruction_body(match.group(2))


def normalize_instruction_body(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def instruction_revision(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def normalize_open_findings_for_live_state(bridge_text: str) -> str:
    """Drop stale ACK-mismatch findings once the live ACK is current."""
    snapshot = extract_bridge_snapshot(bridge_text)
    open_findings = snapshot.sections.get(_OPEN_FINDINGS_HEADING, "").strip()
    if not open_findings:
        return bridge_text

    liveness = summarize_bridge_liveness(snapshot)
    normalized_findings = prune_resolved_open_findings(
        open_findings=open_findings,
        claude_ack_current=liveness.claude_ack_current,
    )
    if normalized_findings == open_findings:
        return bridge_text

    return _replace_section(
        bridge_text,
        heading=_OPEN_FINDINGS_HEADING,
        body=normalized_findings,
    )


def prune_resolved_open_findings(
    *,
    open_findings: str,
    claude_ack_current: bool,
) -> str:
    if not claude_ack_current:
        return open_findings
    items = split_markdown_items(open_findings)
    kept = [item for item in items if not is_ack_stale_finding(item)]
    if not kept:
        return "- none"
    return "\n".join(kept)


def split_markdown_items(text: str) -> list[str]:
    """Split a markdown list body into top-level bullet blocks."""
    lines = text.splitlines()
    if not any(line.lstrip().startswith("- ") for line in lines):
        return [text.strip()] if text.strip() else []

    items: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.lstrip().startswith("- "):
            if current:
                items.append(current)
            current = [line]
            continue
        if current:
            current.append(line)

    if current:
        items.append(current)
    return ["\n".join(block).strip() for block in items if "\n".join(block).strip()]


def is_ack_stale_finding(item: str) -> bool:
    lower = item.lower()
    if "claude ack" not in lower:
        return False
    return (
        "stale" in lower
        or "does not match" in lower
        or "instruction revision" in lower
        or "instruction-rev" in lower
    )


def _replace_section(text: str, *, heading: str, body: str) -> str:
    pattern = SECTION_RE_TEMPLATE.format(heading=re.escape(heading))

    def replacement(match: re.Match[str]) -> str:
        return f"{match.group(1)}{body}\n\n"

    return re.sub(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)
