"""Tests for the ReviewerObservation contract and its builder."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime.reviewer_observation import (
    STATUS_ACCEPTED,
    STATUS_NOT_SEEN,
    STATUS_PENDING_REVIEW,
    STATUS_UNDER_REVIEW,
    ReviewerObservation,
    resolve_reviewer_observation,
)


class TestResolveReviewerObservation(unittest.TestCase):
    """Verify status derivation for all key scenarios."""

    def test_not_seen_when_stale(self) -> None:
        """Stale reviewer freshness produces not_seen status."""
        obs = resolve_reviewer_observation(
            head_sha="abc123",
            last_codex_poll_utc="",
            reviewer_freshness="stale",
            review_needed=True,
            reviewed_hash_current=False,
            last_reviewed_sha="",
            head_at_push_time="",
            review_accepted=False,
        )
        self.assertEqual(obs.status, STATUS_NOT_SEEN)
        self.assertTrue(obs.stale)
        self.assertTrue(obs.review_needed)

    def test_not_seen_when_freshness_is_dashes(self) -> None:
        """Default freshness '--' treated as stale."""
        obs = resolve_reviewer_observation(
            head_sha="abc123",
            last_codex_poll_utc="",
            reviewer_freshness="--",
            review_needed=True,
            reviewed_hash_current=False,
            last_reviewed_sha="",
            head_at_push_time="",
            review_accepted=False,
        )
        self.assertEqual(obs.status, STATUS_NOT_SEEN)
        self.assertTrue(obs.stale)

    def test_not_seen_when_poll_utc_empty(self) -> None:
        """Empty poll UTC means Codex never polled."""
        obs = resolve_reviewer_observation(
            head_sha="abc123",
            last_codex_poll_utc="",
            reviewer_freshness="5m ago",
            review_needed=True,
            reviewed_hash_current=False,
            last_reviewed_sha="",
            head_at_push_time="",
            review_accepted=False,
        )
        self.assertEqual(obs.status, STATUS_NOT_SEEN)
        self.assertTrue(obs.stale)

    def test_pending_review_when_fresh_but_unreviewed(self) -> None:
        """Fresh poll with review_needed=True and not accepted gives pending_review."""
        obs = resolve_reviewer_observation(
            head_sha="abc123",
            last_codex_poll_utc="2026-04-05T12:00:00Z",
            reviewer_freshness="2m ago",
            review_needed=True,
            reviewed_hash_current=True,
            last_reviewed_sha="def456",
            head_at_push_time="def456",
            review_accepted=False,
        )
        self.assertEqual(obs.status, STATUS_PENDING_REVIEW)
        self.assertFalse(obs.stale)
        self.assertTrue(obs.review_needed)

    def test_accepted_when_hash_current(self) -> None:
        """review_accepted=True with reviewed_hash_current=True gives accepted."""
        obs = resolve_reviewer_observation(
            head_sha="abc123",
            last_codex_poll_utc="2026-04-05T12:00:00Z",
            reviewer_freshness="1m ago",
            review_needed=False,
            reviewed_hash_current=True,
            last_reviewed_sha="abc123",
            head_at_push_time="abc123",
            review_accepted=True,
        )
        self.assertEqual(obs.status, STATUS_ACCEPTED)
        self.assertFalse(obs.stale)
        self.assertFalse(obs.review_needed)
        self.assertTrue(obs.reviewed_hash_current)

    def test_under_review_when_hash_drifted(self) -> None:
        """Fresh, not accepted, hash not current gives under_review."""
        obs = resolve_reviewer_observation(
            head_sha="abc123",
            last_codex_poll_utc="2026-04-05T12:00:00Z",
            reviewer_freshness="30s ago",
            review_needed=False,
            reviewed_hash_current=False,
            last_reviewed_sha="def456",
            head_at_push_time="def456",
            review_accepted=False,
        )
        self.assertEqual(obs.status, STATUS_UNDER_REVIEW)
        self.assertFalse(obs.stale)

    def test_accepted_overrides_review_needed(self) -> None:
        """Accepted with hash current wins even if review_needed is True."""
        obs = resolve_reviewer_observation(
            head_sha="abc123",
            last_codex_poll_utc="2026-04-05T12:00:00Z",
            reviewer_freshness="1m ago",
            review_needed=True,
            reviewed_hash_current=True,
            last_reviewed_sha="abc123",
            head_at_push_time="abc123",
            review_accepted=True,
        )
        self.assertEqual(obs.status, STATUS_ACCEPTED)

    def test_frozen_dataclass(self) -> None:
        """ReviewerObservation is immutable."""
        obs = resolve_reviewer_observation(
            head_sha="abc123",
            last_codex_poll_utc="2026-04-05T12:00:00Z",
            reviewer_freshness="1m ago",
            review_needed=False,
            reviewed_hash_current=True,
            last_reviewed_sha="abc123",
            head_at_push_time="abc123",
            review_accepted=True,
        )
        with self.assertRaises(AttributeError):
            obs.status = "mutated"  # type: ignore[misc]

    def test_head_sha_preserved(self) -> None:
        """head_sha and observed_head_sha are stored correctly."""
        obs = resolve_reviewer_observation(
            head_sha="head1",
            last_codex_poll_utc="2026-04-05T12:00:00Z",
            reviewer_freshness="1m ago",
            review_needed=True,
            reviewed_hash_current=False,
            last_reviewed_sha="reviewed1",
            head_at_push_time="push1",
            review_accepted=False,
        )
        self.assertEqual(obs.head_sha, "head1")
        self.assertEqual(obs.observed_head_sha, "push1")
        self.assertEqual(obs.last_reviewed_sha, "reviewed1")


if __name__ == "__main__":
    unittest.main()
