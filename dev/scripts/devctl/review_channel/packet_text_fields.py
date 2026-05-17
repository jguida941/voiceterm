"""Text normalization helpers for review-packet contract fields."""

from __future__ import annotations

import re

_MP_ID_RE = re.compile(r"^MP-\d+$", re.IGNORECASE)
_PLAN_TASK_RE = re.compile(r"^MP\d+-P\d+(?:-T\d+[A-Z]*(?:-[A-Z])?)?$", re.IGNORECASE)
_PACKET_ID_RE = re.compile(r"^rev_pkt_\d+$", re.IGNORECASE)
_ANCHOR_PREFIX_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*:")


def clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_string_rows(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    rows: list[str] = []
    for entry in value:
        text = str(entry).strip()
        if text:
            rows.append(text)
    return rows


def normalize_anchor_ref_rows(value: object) -> list[str]:
    return [canonical_anchor_ref(text) for text in normalize_string_rows(value)]


def canonical_anchor_ref(value: str) -> str:
    """Accept operator vocabulary and store canonical typed anchor refs."""
    text = value.strip()
    if _ANCHOR_PREFIX_RE.match(text):
        return text
    if _PACKET_ID_RE.fullmatch(text):
        return f"packet:{text.lower()}"
    if _PLAN_TASK_RE.fullmatch(text):
        return f"checklist:{text.upper()}"
    if _MP_ID_RE.fullmatch(text):
        return f"section:{text.upper()}"
    return text
