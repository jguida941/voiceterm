"""Semantic idempotency for review-channel packet posts."""

from __future__ import annotations

import json
from collections.abc import Iterable

# Lifecycle states that consume the semantic retry slot. Mirrors the canonical
# action mapping at ``packet_lifecycle.py::_ACTION_BY_EVENT_TYPE`` and the
# Codex-locked policy in rev_pkt_2247:
# - "applied": packet reached terminal-success disposition
# - "pending"/"acked": packet is still in-flight; original is the live retry slot
# - "apply_pending_after_execution": handoff still needs explicit
#   apply/dismiss/failure closure before the actor is considered free
# Lifecycle states that leave the retry slot OPEN (terminal non-success):
# - "dismissed": packet was rejected; retry permitted
# - "archived":  packet timed out (packet_expired); retry permitted
# - "failed":    action_request execution failed; retry permitted
_RETRY_SLOT_CONSUMING_STATUSES = frozenset(
    {
        "pending",
        "acked",
        "applied",
        "apply_pending_after_execution",
    }
)

PACKET_POST_IDEMPOTENCY_FIELDS = (
    "from_agent",
    "to_agent",
    "kind",
    "summary",
    "body",
    "requested_action",
    "policy_hint",
    "approval_required",
    "target_kind",
    "target_ref",
    "target_revision",
    "target_role",
    "target_session_id",
    "requested_session_visibility",
    "release_mode",
    "release_commit_count",
    "anchor_refs",
    "intake_ref",
    "mutation_op",
    "pipeline_generation",
    "staged_snapshot_hash",
    "guard_results_summary",
    "full_guard_bundle_evidence",
)


def packet_posted_idempotency_key(event: dict[str, object], key_builder) -> str:
    """Return a duplicate-suppression key over semantic packet content."""
    payload: dict[str, object] = {}
    for field in PACKET_POST_IDEMPOTENCY_FIELDS:
        value = event.get(field)
        if value in (None, "", [], ()):
            continue
        payload[field] = value
    return key_builder(
        "packet_posted",
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
    )


def is_idempotency_consumed_by(
    events: Iterable[dict[str, object]],
    idempotency_key: str,
    *,
    current_event_type: str = "",
) -> bool:
    """Decide whether prior events consume the semantic retry slot for ``idempotency_key``.

    Symmetric strictness is required per Codex rev_pkt_2255:

    - **Current event is NOT packet_posted** (liveness / transition / daemon /
      side ledger): any prior match rejects, regardless of prior packet
      lifecycle. Non-packet writes have their own dedupe contract that does
      not consume a packet retry slot — but two distinct non-packet writes
      colliding on the same key represents a programming bug, not a retry.
    - **Current event IS packet_posted**: lifecycle-aware. A prior non-packet
      match still rejects (the key is already in use as a non-packet
      identifier). A prior packet_posted match rejects only when the matched
      packet's lifecycle is one of {pending, acked, applied,
      apply_pending_after_execution} per rev_pkt_2247. Packets in
      {dismissed, failed, archived/expired} leave the retry slot open.

    Pass ``current_event_type`` from ``event.get('event_type')`` at the call
    site. Empty string defaults to packet-posted semantics for back-compat
    with callers that have not been updated.
    """
    if not idempotency_key:
        return False

    matched_packet_ids: list[str] = []
    non_packet_match = False
    for event in events:
        if str(event.get("idempotency_key") or "").strip() != idempotency_key:
            continue
        if str(event.get("event_type") or "") == "packet_posted":
            packet_id = str(event.get("packet_id") or "").strip()
            if packet_id:
                matched_packet_ids.append(packet_id)
        else:
            non_packet_match = True

    # Symmetric non-packet strictness per rev_pkt_2255: when the CURRENT event
    # is not packet_posted, any prior match (packet or non-packet) rejects.
    # Packet retry-slot semantics only apply when both sides are packets.
    is_current_packet_post = (
        not current_event_type or current_event_type == "packet_posted"
    )
    if not is_current_packet_post:
        return non_packet_match or bool(matched_packet_ids)

    # Current is packet_posted. Prior non-packet match always rejects.
    if non_packet_match:
        return True

    if not matched_packet_ids:
        return False

    events_list = list(events) if not isinstance(events, list) else events
    return is_idempotency_consumed_by_statuses(
        non_packet_match=non_packet_match,
        matched_packet_statuses=(
            _latest_packet_status(events_list, packet_id)
            for packet_id in matched_packet_ids
        ),
        current_event_type=current_event_type,
    )


def is_idempotency_consumed_by_statuses(
    *,
    non_packet_match: bool,
    matched_packet_statuses: Iterable[str],
    current_event_type: str = "",
) -> bool:
    """Apply packet retry-slot policy to a precomputed idempotency index."""
    statuses = tuple(matched_packet_statuses)
    is_current_packet_post = (
        not current_event_type or current_event_type == "packet_posted"
    )
    if not is_current_packet_post:
        return non_packet_match or bool(statuses)

    if non_packet_match:
        return True

    return any(
        status in _RETRY_SLOT_CONSUMING_STATUSES
        for status in statuses
    )


def _latest_packet_status(
    events: list[dict[str, object]],
    packet_id: str,
) -> str:
    """Return the most recent lifecycle status observed for ``packet_id``.

    Walks events in append order. ``packet_posted`` initializes status to
    ``pending``; transition events advance it. Returns ``""`` if no event
    references this packet.
    """
    status = ""
    for event in events:
        if str(event.get("packet_id") or "").strip() != packet_id:
            continue
        event_type = str(event.get("event_type") or "")
        if event_type == "packet_posted":
            status = "pending"
        elif event_type == "packet_acked":
            status = "acked"
        elif event_type == "packet_dismissed":
            status = "dismissed"
        elif event_type == "packet_applied":
            status = "applied"
        elif event_type == "packet_expired":
            status = "archived"
        elif event_type == "action_request_execution_failed":
            status = "failed"
        elif event_type == "action_request_apply_pending_after_execution":
            status = "apply_pending_after_execution"
    return status
