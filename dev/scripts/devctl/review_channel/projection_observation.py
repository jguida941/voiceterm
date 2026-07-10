"""Build reviewer-observation projection dicts for compact.json and review_state.json."""

from __future__ import annotations

from typing import Any


def build_observation_projection(review_state: dict[str, object]) -> dict[str, object] | None:
    """Derive a reviewer-observation dict from review_state bridge data.

    Returns None when bridge data is absent or lacks the fields needed
    to produce a meaningful observation.
    """
    bridge = review_state.get("bridge")
    if not isinstance(bridge, dict):
        return None

    from ..runtime.reviewer_observation import resolve_reviewer_observation

    poll_utc = str(bridge.get("last_codex_poll_utc") or "").strip()
    review_needed = bool(bridge.get("review_needed", True))
    reviewed_hash_current = bool(bridge.get("reviewed_hash_current", False))

    reviewer_runtime = review_state.get("reviewer_runtime")
    head_at_push_time = _extract_head_at_push_time(bridge, reviewer_runtime)
    review_accepted = _extract_review_accepted(reviewer_runtime)

    reviewer_freshness = _extract_typed_freshness(reviewer_runtime, poll_utc)

    obs = resolve_reviewer_observation(
        head_sha="",
        last_codex_poll_utc=poll_utc,
        reviewer_freshness=reviewer_freshness,
        review_needed=review_needed,
        reviewed_hash_current=reviewed_hash_current,
        last_reviewed_sha=head_at_push_time,
        head_at_push_time=head_at_push_time,
        review_accepted=review_accepted,
    )
    return {
        "status": obs.status,
        "observed_head_sha": obs.observed_head_sha,
        "observed_at_utc": obs.observed_at_utc,
        "review_needed": obs.review_needed,
        "stale": obs.stale,
    }


def _extract_review_accepted(reviewer_runtime: Any) -> bool:
    """Extract review_accepted from reviewer_runtime dict."""
    if not isinstance(reviewer_runtime, dict):
        return False
    acceptance = reviewer_runtime.get("review_acceptance")
    if not isinstance(acceptance, dict):
        return False
    raw = acceptance.get("review_accepted")
    if isinstance(raw, bool):
        return raw
    verdict = str(acceptance.get("current_verdict") or "").strip().lower()
    return verdict in ("accepted", "approved", "pass")


def _extract_head_at_push_time(bridge: dict[str, Any], reviewer_runtime: Any) -> str:
    """Extract head_at_push_time from the best available typed source.

    Checks: (1) bridge state dict, (2) reviewer_runtime metadata,
    (3) reviewer_runtime.review_acceptance. Returns empty string when
    no source carries the field.
    """
    val = str(bridge.get("head_at_push_time") or "").strip()
    if val:
        return val
    if isinstance(reviewer_runtime, dict):
        val = str(reviewer_runtime.get("head_at_push_time") or "").strip()
        if val:
            return val
        meta = reviewer_runtime.get("reviewer_metadata")
        if isinstance(meta, dict):
            val = str(meta.get("head_at_push_time") or "").strip()
            if val:
                return val
    return ""


def _extract_typed_freshness(reviewer_runtime: Any, poll_utc: str) -> str:
    """Extract typed reviewer_freshness from reviewer_runtime dict.

    Falls back to "--" when no typed freshness is available instead of
    assuming "fresh" from the existence of a poll timestamp.
    """
    if isinstance(reviewer_runtime, dict):
        typed = str(reviewer_runtime.get("reviewer_freshness") or "").strip()
        if typed:
            return typed
    if not poll_utc:
        return "--"
    return "stale"
