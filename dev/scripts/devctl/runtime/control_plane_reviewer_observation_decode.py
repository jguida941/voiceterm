"""Deserialize reviewer observation payloads for control-plane snapshots."""

from __future__ import annotations

from .reviewer_observation import ReviewerObservation
from .value_coercion import coerce_bool, coerce_string


def observation_from_mapping(raw: object) -> ReviewerObservation | None:
    """Deserialize a ReviewerObservation from a JSON-like mapping."""
    if not isinstance(raw, dict):
        return None
    return ReviewerObservation(
        head_sha=coerce_string(raw.get("head_sha")),
        observed_head_sha=coerce_string(raw.get("observed_head_sha")),
        observed_at_utc=coerce_string(raw.get("observed_at_utc")),
        last_reviewed_sha=coerce_string(raw.get("last_reviewed_sha")),
        status=coerce_string(raw.get("status")) or "not_seen",
        review_needed=coerce_bool(raw.get("review_needed", True)),
        reviewed_hash_current=coerce_bool(raw.get("reviewed_hash_current", False)),
        stale=coerce_bool(raw.get("stale", True)),
    )
