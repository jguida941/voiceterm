"""Shared packet predicates for review-only notices."""

from __future__ import annotations

from collections.abc import Mapping


def is_review_only_notice(packet: Mapping[str, object], *, kind: str) -> bool:
    """Return whether a packet is only a review notice, not durable intent."""
    if kind != "system_notice":
        return False
    if _text(packet.get("target_kind")) or _text(packet.get("target_ref")):
        return False
    if isinstance(packet.get("plan_proposal"), Mapping):
        return False
    return _text(packet.get("requested_action")) == "review_only" or (
        _text(packet.get("policy_hint")) == "review_only"
    )


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["is_review_only_notice"]
