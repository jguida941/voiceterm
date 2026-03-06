"""Shared metadata parsing helpers for ADR hygiene audits."""

from __future__ import annotations

import re
from pathlib import Path

ALLOWED_ADR_STATUSES = {"Proposed", "Accepted", "Deprecated", "Superseded"}
ADR_INDEX_LINK_RE = re.compile(r"\[(\d{4})\]\(([^)]+)\)")
ADR_INDEX_ROW_RE = re.compile(r"\|\s*\[(\d{4})\]\([^)]+\)\s*\|[^|]*\|\s*([A-Za-z]+)\s*\|")
ADR_NEXT_RE = re.compile(r"\bnext:\s*(\d{4})\b", flags=re.IGNORECASE)
ADR_IDS_LINE_RE_TEMPLATE = r"^\s*{label}\s*:\s*(.+?)\s*$"
ADR_ID_OR_RANGE_RE = re.compile(r"\b(\d{4})(?:\s*-\s*(\d{4}))?\b")
ADR_REF_RE = re.compile(r"ADR-(\d{4})")
ADR_STATIC_COUNT_RE = re.compile(r"\b\d+\s+ADRs\b")
ADR_WILDCARD_RANGE_RE = re.compile(r"dev/adr/\d{4}-\*\.md")
MASTER_ADR_BACKLOG_HEADING = "## ADR Program Backlog (Cross-Plan, Pending)"
AUTONOMY_ADR_BACKLOG_HEADING = "### 3.6 ADR Backlog (Required for Scope Control)"
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ADR_REFERENCE_SCAN_FILES = (
    "dev/active/theme_upgrade.md",
    "dev/history/ENGINEERING_EVOLUTION.md",
)


def extract_field(text: str, field: str) -> str:
    """Read `Field: value` metadata from markdown files."""
    match = re.search(rf"^{re.escape(field)}:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def format_adr_ids(values: list[int]) -> str:
    """Render integer ADR ids as zero-padded values."""
    return ", ".join(f"{value:04d}" for value in values)


def parse_adr_id_ranges(raw_value: str, *, label: str, errors: list[str]) -> set[int]:
    """Parse `0001, 0002-0004` style ADR id lists into a set of ints."""
    parsed: set[int] = set()
    matches = list(ADR_ID_OR_RANGE_RE.finditer(raw_value))
    if not matches and raw_value.strip().lower() != "none":
        errors.append(
            f"{label} line is present but has no ADR ids/ranges: {raw_value!r}."
        )
        return parsed

    for match in matches:
        start = int(match.group(1))
        end_text = match.group(2)
        end = int(end_text) if end_text else start
        if end < start:
            errors.append(
                f"{label} range is descending and invalid: {start:04d}-{end:04d}."
            )
            continue
        parsed.update(range(start, end + 1))
    return parsed


def parse_governed_adr_ids(
    index_text: str,
    *,
    label: str,
    errors: list[str],
) -> set[int]:
    """Extract one ADR id/range metadata line from ADR README content."""
    pattern = re.compile(
        ADR_IDS_LINE_RE_TEMPLATE.format(label=re.escape(label)),
        flags=re.MULTILINE,
    )
    match = pattern.search(index_text)
    if not match:
        return set()
    return parse_adr_id_ranges(match.group(1), label=label, errors=errors)


def extract_markdown_section(text: str, heading: str) -> str:
    """Return markdown text under `heading` until the next same-or-higher heading."""
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == heading:
            start = idx + 1
            break
    if start is None:
        return ""

    heading_level = len(heading.split(" ", maxsplit=1)[0])
    end = len(lines)
    for idx in range(start, len(lines)):
        candidate = lines[idx].strip()
        if not candidate.startswith("#"):
            continue
        level = len(candidate) - len(candidate.lstrip("#"))
        if level <= heading_level:
            end = idx
            break
    return "\n".join(lines[start:end])


def scan_stale_adr_reference_patterns(repo_root: Path) -> list[dict]:
    """Find stale ADR count/range claims in long-lived governance docs."""
    violations: list[dict] = []
    for relative in ADR_REFERENCE_SCAN_FILES:
        path = repo_root / relative
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if ADR_STATIC_COUNT_RE.search(line):
                violations.append(
                    {
                        "file": relative,
                        "line": lineno,
                        "rule": "static-adr-count",
                        "line_text": line.strip(),
                    }
                )
            if ADR_WILDCARD_RANGE_RE.search(line):
                violations.append(
                    {
                        "file": relative,
                        "line": lineno,
                        "rule": "adr-wildcard-range",
                        "line_text": line.strip(),
                    }
                )
    return violations
