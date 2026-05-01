"""Shared message text extraction for rollout session parsers."""

from __future__ import annotations

from typing import Any


def extract_message_text(payload: dict[str, Any]) -> str:
    """Flatten a message payload's content into a single text string."""
    content = payload.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for entry in content:
            if isinstance(entry, dict):
                text = entry.get("text") or entry.get("content") or ""
                if isinstance(text, str) and text:
                    parts.append(text)
        return " ".join(parts)
    return ""


__all__ = ["extract_message_text"]
