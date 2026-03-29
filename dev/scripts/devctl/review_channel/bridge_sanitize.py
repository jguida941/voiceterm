"""Bridge section sanitization and text-cleaning helpers.

This module owns the shared bridge hygiene and live-section sanitization logic
so the compatibility renderer can stay thin.
"""

from __future__ import annotations

import re

from .bridge_section_validation import find_embedded_markdown_headings
from .bridge_text_cleanup import (
    collapse_blank_lines,
    find_transcript_lines,
    has_ansi_escape,
    has_control_chars,
    is_transcript_line,
    strip_terminal_bytes,
    strip_transcript_lines,
)
from .handoff import extract_bridge_snapshot

BRIDGE_ALLOWED_H2 = (
    "Start-Of-Conversation Rules",
    "Protocol",
    "Swarm Mode",
    "Poll Status",
    "Current Verdict",
    "Open Findings",
    "Claude Status",
    "Claude Questions",
    "Claude Ack",
    "Current Instruction For Claude",
    "Last Reviewed Scope",
)
BRIDGE_REQUIRED_H2 = (
    "Start-Of-Conversation Rules",
    "Protocol",
    "Poll Status",
    "Current Verdict",
    "Open Findings",
    "Claude Status",
    "Claude Questions",
    "Claude Ack",
    "Current Instruction For Claude",
    "Last Reviewed Scope",
)
_BRIDGE_SECTION_LINE_LIMIT_ITEMS = (
    ("Poll Status", 6),
    ("Current Verdict", 8),
    ("Open Findings", 16),
    ("Claude Status", 40),
    ("Claude Questions", 8),
    ("Claude Ack", 16),
    ("Current Instruction For Claude", 12),
    ("Last Reviewed Scope", 16),
)
BRIDGE_SECTION_LINE_LIMITS = dict(_BRIDGE_SECTION_LINE_LIMIT_ITEMS)
MAX_BRIDGE_LINES = 400
MAX_BRIDGE_BYTES = 24_000

_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

_STATUS_HISTORY_MARKERS = (
    "prior slice",
    "prior rev",
    "session ",
    "superseded",
    "hold steady",
)
_QUESTION_DEFAULT = "- None recorded."


def bridge_hygiene_errors(text: str) -> list[str]:
    """Return fail-closed bridge hygiene errors."""
    errors: list[str] = []
    line_count = len(text.splitlines())
    byte_count = len(text.encode("utf-8"))
    if line_count > MAX_BRIDGE_LINES:
        errors.append(
            f"Bridge exceeds the {MAX_BRIDGE_LINES}-line hard limit ({line_count} lines)."
        )
    if byte_count > MAX_BRIDGE_BYTES:
        errors.append(
            f"Bridge exceeds the {MAX_BRIDGE_BYTES}-byte hard limit ({byte_count} bytes)."
        )

    headings = [match.group(1).strip() for match in _H2_RE.finditer(text)]
    duplicates = _duplicate_headings(headings)
    if duplicates:
        errors.append("Bridge contains duplicate H2 headings: " + ", ".join(duplicates))
    unknown = [heading for heading in headings if heading not in BRIDGE_ALLOWED_H2]
    if unknown:
        errors.append(
            "Bridge contains unsupported H2 headings: "
            + ", ".join(sorted(set(unknown)))
        )

    if has_ansi_escape(text):
        errors.append("Bridge contains ANSI escape sequences or terminal control output.")
    if has_control_chars(text):
        errors.append("Bridge contains raw control characters.")

    transcript_hits = find_transcript_lines(text)
    if transcript_hits:
        errors.append(
            "Bridge contains transcript/test-output lines: "
            + "; ".join(f"`{line}`" for line in transcript_hits[:3])
        )

    snapshot = extract_bridge_snapshot(text)
    for heading, limit in BRIDGE_SECTION_LINE_LIMITS.items():
        body = snapshot.sections.get(heading, "").strip()
        if not body:
            continue
        lines = len(body.splitlines())
        if lines > limit:
            errors.append(
                f"`{heading}` exceeds the {limit}-line live-state limit ({lines} lines)."
            )
        heading_hits = find_embedded_markdown_headings(body)
        if heading_hits:
            errors.append(
                f"`{heading}` contains embedded markdown headings: "
                + "; ".join(f"`{line}`" for line in heading_hits)
            )
    return errors


def sanitize_bridge_sections(
    sections: dict[str, str],
    *,
    section_line_limits: dict[str, int],
) -> tuple[dict[str, str], list[str]]:
    """Sanitize all live bridge sections, returning cleaned sections and mutation list."""
    sanitized: dict[str, str] = {}
    mutated: list[str] = []

    sanitized["Poll Status"] = _sanitize_simple_section(
        sections.get("Poll Status", ""),
        default="- Reviewer state unavailable.",
        max_items=2,
        max_lines=section_line_limits["Poll Status"],
    )
    sanitized["Current Verdict"] = _sanitize_simple_section(
        sections.get("Current Verdict", ""),
        default="- reviewer state unavailable",
        max_items=2,
        max_lines=section_line_limits["Current Verdict"],
    )
    sanitized["Open Findings"] = _sanitize_simple_section(
        sections.get("Open Findings", ""),
        default="- none",
        max_items=6,
        max_lines=section_line_limits["Open Findings"],
    )
    sanitized["Current Instruction For Claude"] = _sanitize_simple_section(
        sections.get("Current Instruction For Claude", ""),
        default="- Await reviewer instruction refresh.",
        max_items=4,
        max_lines=section_line_limits["Current Instruction For Claude"],
    )
    sanitized["Claude Status"] = _sanitize_claude_status(
        sections.get("Claude Status", ""),
        max_lines=section_line_limits["Claude Status"],
    )
    sanitized["Claude Questions"] = _sanitize_simple_section(
        sections.get("Claude Questions", ""),
        default=_QUESTION_DEFAULT,
        max_items=3,
        max_lines=section_line_limits["Claude Questions"],
    )
    sanitized["Claude Ack"] = _sanitize_claude_ack(
        sections.get("Claude Ack", ""),
        max_lines=section_line_limits["Claude Ack"],
    )
    sanitized["Last Reviewed Scope"] = _sanitize_simple_section(
        sections.get("Last Reviewed Scope", ""),
        default="- (missing)",
        max_items=12,
        max_lines=section_line_limits["Last Reviewed Scope"],
    )

    for heading, body in sanitized.items():
        previous = sections.get(heading, "").strip()
        if body != (previous or body):
            mutated.append(heading)
    return sanitized, mutated
def _sanitize_simple_section(
    raw: str,
    *,
    default: str,
    max_items: int,
    max_lines: int,
) -> str:
    blocks = _sanitize_blocks(_split_markdown_items(raw))
    if not blocks:
        return default
    kept = _take_blocks(blocks, max_items=max_items, max_lines=max_lines)
    return "\n".join(kept) if kept else default


def _sanitize_claude_status(raw: str, *, max_lines: int) -> str:
    blocks = _sanitize_blocks(_split_markdown_items(raw))
    kept: list[str] = []
    for block in blocks:
        lowered = block.lower()
        if kept and any(marker in lowered for marker in _STATUS_HISTORY_MARKERS):
            break
        kept.append(block)
    kept = _take_blocks(kept, max_items=10, max_lines=max_lines)
    return "\n".join(kept) if kept else "- Status unavailable."


def _sanitize_claude_ack(raw: str, *, max_lines: int) -> str:
    blocks = _sanitize_blocks(_split_markdown_items(raw))
    if not blocks:
        return "- missing"
    kept = [blocks[0]]
    for block in blocks[1:]:
        lowered = block.lower()
        if "instruction-rev:" in lowered:
            break
        if any(marker in lowered for marker in _STATUS_HISTORY_MARKERS):
            break
        kept.append(block)
    kept = _take_blocks(kept, max_items=3, max_lines=max_lines)
    return "\n".join(kept) if kept else "- missing"


def _sanitize_blocks(blocks: list[str]) -> list[str]:
    cleaned: list[str] = []
    for block in blocks:
        normalized = strip_transcript_lines(strip_terminal_bytes(block)).strip()
        if not normalized:
            continue
        if any(
            is_transcript_line(line.strip())
            for line in normalized.splitlines()
        ):
            continue
        cleaned.append(normalized)
    return cleaned

def _split_markdown_items(text: str) -> list[str]:
    lines = collapse_blank_lines(strip_terminal_bytes(text).splitlines())
    if not any(line.lstrip().startswith("- ") for line in lines):
        normalized = "\n".join(line.rstrip() for line in lines).strip()
        return [normalized] if normalized else []

    items: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.lstrip().startswith("- "):
            if current:
                items.append(current)
            current = [line.rstrip()]
            continue
        if current:
            current.append(line.rstrip())
    if current:
        items.append(current)
    return ["\n".join(block).strip() for block in items if "\n".join(block).strip()]


def _take_blocks(
    blocks: list[str],
    *,
    max_items: int,
    max_lines: int,
) -> list[str]:
    kept: list[str] = []
    used_lines = 0
    for block in blocks[:max_items]:
        block_lines = len(block.splitlines())
        if kept and used_lines + block_lines > max_lines:
            break
        if not kept and block_lines > max_lines:
            kept.append("\n".join(block.splitlines()[:max_lines]))
            break
        kept.append(block)
        used_lines += block_lines
    return kept
def _duplicate_headings(headings: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for heading in headings:
        if heading in seen and heading not in duplicates:
            duplicates.append(heading)
        seen.add(heading)
    return duplicates
