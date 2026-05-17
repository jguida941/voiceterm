"""Shared small helpers for plan-intent ingestion."""

from __future__ import annotations

from typing import Any


def text(value: object) -> str:
    """Return a stripped string for loose CLI/review-state values."""
    return str(value or "").strip()


def target_ref_from_source(args: Any, source: Any) -> str:
    """Resolve the typed target ref from CLI arguments or packet metadata."""
    packet = source.packet_payload
    return (
        text(getattr(args, "target_ref", ""))
        or text(packet.get("target_ref"))
        or text(packet.get("plan_id"))
    )


__all__ = ["target_ref_from_source", "text"]
