"""Small text-formatting helpers shared across devctl surfaces."""

from __future__ import annotations

from typing import Any


def truncate_text(value: Any, max_chars: int) -> str:
    text = str(value or "").strip()
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
