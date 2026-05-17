"""Typed reviewer-observation record derived from repo-owned state.

Answers: "Has Codex seen this HEAD? Is it pending review, under review,
or accepted?" -- derived entirely from typed inputs (ControlPlaneReadModel
fields, review_state bridge data), NOT from bridge prose parsing.
"""

from __future__ import annotations

from dataclasses import dataclass

REVIEWER_OBSERVATION_CONTRACT_ID = "ReviewerObservation"
REVIEWER_OBSERVATION_SCHEMA_VERSION = 1

# Valid status values for type-safe consumers
STATUS_NOT_SEEN = "not_seen"
STATUS_PENDING_REVIEW = "pending_review"
STATUS_UNDER_REVIEW = "under_review"
STATUS_ACCEPTED = "accepted"


@dataclass(frozen=True)
class ReviewerObservation:
    """Typed reviewer-observation record derived from repo-owned state."""

    head_sha: str                    # current HEAD
    observed_head_sha: str           # HEAD that reviewer last polled/saw
    observed_at_utc: str             # when reviewer last polled
    last_reviewed_sha: str           # HEAD at last accepted review
    status: str                      # "not_seen" | "pending_review" | "under_review" | "accepted"
    review_needed: bool              # whether current HEAD needs review
    reviewed_hash_current: bool      # whether reviewed hash matches current tree
    stale: bool                      # whether reviewer poll is stale


def resolve_reviewer_observation(
    *,
    head_sha: str,
    last_codex_poll_utc: str,
    reviewer_freshness: str,
    review_needed: bool,
    reviewed_hash_current: bool,
    last_reviewed_sha: str,
    head_at_push_time: str,
    review_accepted: bool,
) -> ReviewerObservation:
    """Derive a ReviewerObservation from typed governance inputs.

    Status derivation:
    - stale/empty poll -> "not_seen" (Codex hasn't polled recently)
    - fresh poll, review_needed=True, not accepted -> "pending_review"
    - fresh poll, hash not current, not accepted -> "under_review"
    - accepted and hash current -> "accepted"
    - default fallback -> "pending_review"
    """
    stale = _is_stale(reviewer_freshness, last_codex_poll_utc)
    status = _derive_status(
        stale=stale,
        review_needed=review_needed,
        reviewed_hash_current=reviewed_hash_current,
        review_accepted=review_accepted,
    )
    return ReviewerObservation(
        head_sha=head_sha,
        observed_head_sha=head_at_push_time,
        observed_at_utc=last_codex_poll_utc,
        last_reviewed_sha=last_reviewed_sha,
        status=status,
        review_needed=review_needed,
        reviewed_hash_current=reviewed_hash_current,
        stale=stale,
    )


_NOT_FRESH = frozenset({"stale", "poll_due", "overdue", "--", ""})


def _is_stale(reviewer_freshness: str, last_codex_poll_utc: str) -> bool:
    """Return True when the reviewer poll is not fresh.

    Any freshness value that means "not actively polling" fails closed
    to stale so the observation status becomes ``not_seen``.
    """
    if not last_codex_poll_utc or last_codex_poll_utc.strip() == "":
        return True
    freshness_lower = reviewer_freshness.lower().strip()
    return freshness_lower in _NOT_FRESH


def _derive_status(
    *,
    stale: bool,
    review_needed: bool,
    reviewed_hash_current: bool,
    review_accepted: bool,
) -> str:
    """Derive the observation status from typed boolean inputs."""
    if stale:
        return STATUS_NOT_SEEN
    if review_accepted and reviewed_hash_current:
        return STATUS_ACCEPTED
    if review_needed and not review_accepted:
        return STATUS_PENDING_REVIEW
    if not reviewed_hash_current and not review_accepted:
        return STATUS_UNDER_REVIEW
    return STATUS_PENDING_REVIEW
