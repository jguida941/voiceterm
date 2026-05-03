"""Title helpers for plan-intent rows."""

from __future__ import annotations

import re

from .plan_intake_sources import PlanIntentSource
from .plan_intake_support import text


def source_title(source: PlanIntentSource) -> str:
    """Derive a bounded PlanRow title from packet or markdown text."""
    if source.packet_payload:
        summary = text(source.packet_payload.get("summary"))
        return truncate(f"Packet plan intent: {summary}" if summary else "")
    first_line = next((line.strip() for line in source.body.splitlines() if line.strip()), "")
    return truncate(first_line)


def packet_slug(value: str) -> str:
    """Return the normalized packet id slug used for fallback PlanRows."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    return slug or "UNKNOWN"


def truncate(value: str, limit: int = 240) -> str:
    """Return a single-line bounded title."""
    title = " ".join(value.split())
    return title if len(title) <= limit else f"{title[: limit - 3]}..."


__all__ = ["packet_slug", "source_title", "truncate"]
