"""Shared packet-attention helpers for current-session projections."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_packet_inbox import packet_inbox_from_review_state
from ..runtime.role_profile import TandemRole, default_provider_for_role

_CLEAR_WAKE_REASONS = frozenset({"finding_pending", "expired_unresolved_packet"})


def reviewer_packet_attention_requires_clear(
    review_state: Mapping[str, object],
    reviewer_provider: str = "",
) -> bool:
    """Provider-agnostic check: does the reviewer lane need packet attention cleared?"""
    provider = reviewer_provider or default_provider_for_role(TandemRole.REVIEWER)
    packet_inbox = packet_inbox_from_review_state(review_state)
    record = None if packet_inbox is None else packet_inbox.for_agent(provider)
    return packet_attention_requires_clear(record)


def codex_packet_attention_requires_clear(
    review_state: Mapping[str, object],
) -> bool:
    return reviewer_packet_attention_requires_clear(review_state)


def packet_attention_requires_clear(record: object | None) -> bool:
    if record is None:
        return False
    wake_reason = str(getattr(record, "wake_reason", "") or "").strip()
    has_pending_attention = bool(
        tuple(getattr(record, "pending_actionable_packet_ids", ()) or ())
        or tuple(getattr(record, "expired_unresolved_packet_ids", ()) or ())
        or wake_reason in _CLEAR_WAKE_REASONS
    )
    return bool(
        not str(getattr(record, "current_instruction_packet_id", "") or "").strip()
        and has_pending_attention
    )
