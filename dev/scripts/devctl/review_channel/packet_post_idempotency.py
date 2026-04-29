"""Semantic idempotency for review-channel packet posts."""

from __future__ import annotations

import json

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
