"""Small text-formatting helpers shared across devctl surfaces."""

from __future__ import annotations

from typing import Any


def normalize_inline_markdown(value: str) -> str:
    """Strip common inline markdown wrappers from a short text fragment."""
    normalized = value.strip()
    wrappers = ("**", "__", "`")
    changed = True
    while normalized and changed:
        changed = False
        for wrapper in wrappers:
            if normalized.startswith(wrapper) and normalized.endswith(wrapper):
                normalized = normalized[len(wrapper) : -len(wrapper)].strip()
                changed = True
                break
    return normalized


def truncate_text(value: Any, max_chars: int) -> str:
    text = str(value or "").strip()
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
