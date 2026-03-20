"""Metadata parsing helpers for doc-authority."""

from __future__ import annotations

import re

_METADATA_BOLD_RE = re.compile(
    r"\*\*Status\*\*:\s*(?P<status>[^|]+)"
    r"\|\s*\*\*Last updated\*\*:\s*(?P<updated>[^|]+)"
    r"\|\s*\*\*Owner[:\*]*\*?\*?:?\s*(?P<owner>.+)",
)
_METADATA_PLAIN_RE = re.compile(
    r"Status:\s*(?P<status>[^|]+)"
    r"(?:\|\s*Last updated:\s*(?P<updated>[^|]+))?"
    r"(?:\|\s*Owner:\s*(?P<owner>.+))?",
    re.IGNORECASE,
)
_METADATA_DATE_FIRST_RE = re.compile(
    r"(?P<updated>\d{4}-\d{2}-\d{2})\s*\|\s*(?P<status>[^|]+)"
    r"(?:\|\s*(?P<owner>.+))?",
)


def parse_metadata_header(text: str) -> dict[str, str]:
    """Parse status/updated/owner from the first 10 lines of a doc."""
    for line in text.splitlines()[:10]:
        stripped = line.strip()
        if not stripped:
            continue
        for matcher in (
            _match_bold_metadata,
            _match_date_first_metadata,
            _match_plain_metadata,
        ):
            matched = matcher(stripped)
            if matched:
                return matched
    return {}


def _match_bold_metadata(line: str) -> dict[str, str]:
    match = _METADATA_BOLD_RE.search(line)
    if not match:
        return {}
    return {
        "status": match.group("status").strip().rstrip("|").strip(),
        "updated": match.group("updated").strip().rstrip("|").strip(),
        "owner": match.group("owner").strip(),
    }


def _match_date_first_metadata(line: str) -> dict[str, str]:
    match = _METADATA_DATE_FIRST_RE.search(line)
    if not match:
        return {}
    payload = {
        "updated": match.group("updated").strip(),
        "status": match.group("status").strip().rstrip("|").strip(),
    }
    owner = match.group("owner")
    if owner:
        payload["owner"] = owner.strip()
    return payload


def _match_plain_metadata(line: str) -> dict[str, str]:
    match = _METADATA_PLAIN_RE.search(line)
    if not match:
        return {}
    payload = {
        "status": match.group("status").strip().rstrip("|").strip(),
    }
    updated = match.group("updated")
    owner = match.group("owner")
    if updated:
        payload["updated"] = updated.strip()
    if owner:
        payload["owner"] = owner.strip()
    return payload


def lifecycle_from_meta(meta: dict[str, str]) -> str:
    """Derive lifecycle status from parsed metadata header."""
    status = meta.get("status", "").lower().strip()
    if not status:
        return "unknown"
    if "complete" in status or "closed" in status or "archived" in status:
        return "complete"
    if "active" in status or "execution" in status:
        return "active"
    if "draft" in status:
        return "draft"
    if "deferred" in status or "paused" in status or "parked" in status:
        return "deferred"
    return "active"
