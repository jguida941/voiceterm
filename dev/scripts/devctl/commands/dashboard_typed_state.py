"""Typed ReviewState extraction helpers for the dashboard (Slice D: MP-384).

Each function maps a typed ReviewState dict into the flat shape expected
by downstream dashboard builders, so the data pipeline works identically
regardless of whether the source is compact.json or review_state.json.
"""

from __future__ import annotations

from typing import Any, TypedDict


class SessionFields(TypedDict):
    """Flat session shape matching compact.json's current_session layout."""

    current_instruction: str
    current_instruction_revision: str
    implementer_status: str
    implementer_ack_state: str
    open_findings: str
    last_reviewed_scope: str
    implementer_state_hash: str


class PendingPacketFields(TypedDict):
    """Typed shape for a single pending action packet."""

    packet_id: str
    kind: str
    from_agent: str
    to_agent: str
    summary: str
    status: str
    requested_action: str
    approval_required: bool


def _extract_typed_session(review_state: dict[str, Any]) -> SessionFields:
    """Extract current_session fields from a typed ReviewState dict.

    Maps ReviewState.current_session (ReviewCurrentSessionState) into the
    same flat dict shape that compact.json's current_session provides, so
    downstream builders work unchanged.
    """
    cs = review_state.get("current_session", {})
    return SessionFields(
        current_instruction=cs.get("current_instruction", ""),
        current_instruction_revision=cs.get("current_instruction_revision", ""),
        implementer_status=cs.get("implementer_status", ""),
        implementer_ack_state=cs.get("implementer_ack_state", ""),
        open_findings=cs.get("open_findings", ""),
        last_reviewed_scope=cs.get("last_reviewed_scope", ""),
        implementer_state_hash=cs.get("implementer_state_hash", ""),
    )


def _extract_typed_doctor(review_state: dict[str, Any]) -> dict[str, Any]:
    """Extract doctor/runtime health fields from a typed ReviewState dict.

    ReviewState carries reviewer_runtime.doctor or a top-level doctor key
    depending on the projection version. This function normalizes both shapes.
    """
    rt = review_state.get("reviewer_runtime", {})
    doctor = rt.get("doctor", {}) if isinstance(rt, dict) else {}
    if not doctor:
        doctor = review_state.get("doctor", {})
    return doctor if isinstance(doctor, dict) else {}


def _extract_typed_attention(
    review_state: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Extract attention state from a typed ReviewState dict.

    Returns a flat dict with status, owner, summary, recommended_action, and
    recommended_command. Returns None when ReviewState is absent.
    """
    if review_state is None:
        return None
    attn = review_state.get("attention")
    if not isinstance(attn, dict):
        return None
    return {
        "status": attn.get("status", "n/a"),
        "owner": attn.get("owner", "n/a"),
        "summary": attn.get("summary", "n/a"),
        "recommended_action": attn.get("recommended_action", ""),
        "recommended_command": attn.get("recommended_command", ""),
    }


def _extract_typed_packets(
    review_state: dict[str, Any] | None,
) -> list[PendingPacketFields]:
    """Extract pending action packets from a typed ReviewState dict.

    Returns only packets with status=pending so the dashboard surfaces
    actionable items that need operator or agent attention.
    """
    if review_state is None:
        return []
    packets = review_state.get("packets", [])
    if not isinstance(packets, list):
        return []
    pending: list[PendingPacketFields] = []
    for pkt in packets:
        if not isinstance(pkt, dict):
            continue
        if pkt.get("status") != "pending":
            continue
        pending.append(PendingPacketFields(
            packet_id=pkt.get("packet_id", ""),
            kind=pkt.get("kind", ""),
            from_agent=pkt.get("from_agent", ""),
            to_agent=pkt.get("to_agent", ""),
            summary=pkt.get("summary", ""),
            status="pending",
            requested_action=pkt.get("requested_action", ""),
            approval_required=pkt.get("approval_required", False),
        ))
    return pending
