"""Packet-attention helpers extracted from governed commit runtime support."""

from __future__ import annotations


def _held_lease_active(held_lease: str) -> bool:
    """Return true when the caller is holding a non-empty attention lease."""
    return bool(str(held_lease or "").strip())


def _has_actionable_packet_attention(record: object) -> bool:
    pending_actionable = getattr(record, "pending_actionable_packet_ids", ()) or ()
    if pending_actionable:
        return True
    wake_reason = str(getattr(record, "wake_reason", "") or "").strip()
    return wake_reason == "finding_pending"


def _target_agent_has_actionable_packet_attention(
    *,
    packet_inbox: object,
    target_agent: str,
) -> bool:
    agent_records = tuple(getattr(packet_inbox, "agents", ()) or ())
    if target_agent:
        normalized_target = target_agent.strip().lower()
        for record in agent_records:
            if str(getattr(record, "agent", "") or "").strip().lower() != normalized_target:
                continue
            return _has_actionable_packet_attention(record)
        return False
    return any(_has_actionable_packet_attention(record) for record in agent_records)
