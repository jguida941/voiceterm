"""Tests for publication ownership resolution and action request builder.

Covers topology-to-owner resolution, duplicate prevention, and portable
provider abstraction.
"""

from __future__ import annotations

import unittest

from dev.scripts.devctl.review_channel.publication_ownership import (
    OWNER_BLOCKED,
    OWNER_IMPLEMENTER,
    OWNER_REVIEWER,
    PublicationOwnershipDecision,
    build_implementer_publication_request,
    is_duplicate_publication,
    resolve_publication_owner,
)


class TestResolvePublicationOwner(unittest.TestCase):
    """Test topology-to-owner resolution for all topologies."""

    def test_remote_control_gives_implementer(self):
        decision = resolve_publication_owner(interaction_mode="remote_control")
        self.assertEqual(decision.owner, OWNER_IMPLEMENTER)
        self.assertIn("remote_control", decision.reason)

    def test_local_terminal_default_gives_reviewer(self):
        decision = resolve_publication_owner(
            interaction_mode="local_terminal",
            topology="single_implementer_single_reviewer",
        )
        self.assertEqual(decision.owner, OWNER_REVIEWER)

    def test_dual_implementer_blocked(self):
        decision = resolve_publication_owner(
            interaction_mode="local_terminal",
            topology="dual_implementer",
        )
        self.assertEqual(decision.owner, OWNER_BLOCKED)

    def test_no_live_agents_blocked(self):
        decision = resolve_publication_owner(
            interaction_mode="local_terminal",
            topology="no_live_agents",
        )
        self.assertEqual(decision.owner, OWNER_BLOCKED)

    def test_reviewer_only_blocked(self):
        decision = resolve_publication_owner(
            interaction_mode="local_terminal",
            topology="reviewer_only",
        )
        self.assertEqual(decision.owner, OWNER_BLOCKED)

    def test_solo_implementer_owns(self):
        decision = resolve_publication_owner(
            interaction_mode="local_terminal",
            topology="implementer_without_reviewer",
        )
        self.assertEqual(decision.owner, OWNER_IMPLEMENTER)

    def test_custom_providers_threaded_through(self):
        decision = resolve_publication_owner(
            interaction_mode="remote_control",
            reviewer_provider="gemini",
            implementer_provider="cursor",
        )
        self.assertEqual(decision.owner_provider, "cursor")

    def test_default_providers_from_role_system(self):
        decision = resolve_publication_owner(interaction_mode="remote_control")
        self.assertEqual(decision.owner_provider, "claude")

    def test_serialization(self):
        decision = resolve_publication_owner(interaction_mode="remote_control")
        d = decision.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["owner"], OWNER_IMPLEMENTER)


class TestBuildImplementerPublicationRequest(unittest.TestCase):
    """Test action_request builder for implementer-owned publication."""

    def test_returns_packet_for_implementer_owner(self):
        decision = PublicationOwnershipDecision(
            owner=OWNER_IMPLEMENTER,
            owner_provider="claude",
            reason="remote_control",
        )
        packet = build_implementer_publication_request(
            decision, approved_head_sha="abc123def456",
        )
        self.assertIsNotNone(packet)
        self.assertEqual(packet["kind"], "action_request")
        self.assertEqual(packet["to_agent"], "claude")
        self.assertEqual(packet["requested_action"], "execute_publication")
        self.assertIn("abc123de", packet["summary"])

    def test_returns_none_for_reviewer_owner(self):
        decision = PublicationOwnershipDecision(
            owner=OWNER_REVIEWER,
            owner_provider="codex",
            reason="local_reviewer",
        )
        packet = build_implementer_publication_request(
            decision, approved_head_sha="abc123",
        )
        self.assertIsNone(packet)

    def test_returns_none_for_blocked(self):
        decision = PublicationOwnershipDecision(
            owner=OWNER_BLOCKED,
            owner_provider="",
            reason="blocked",
        )
        packet = build_implementer_publication_request(
            decision, approved_head_sha="abc123",
        )
        self.assertIsNone(packet)

    def test_custom_reviewer_as_from_agent(self):
        decision = PublicationOwnershipDecision(
            owner=OWNER_IMPLEMENTER,
            owner_provider="cursor",
            reason="remote_control",
        )
        packet = build_implementer_publication_request(
            decision,
            approved_head_sha="abc123",
            reviewer_provider="gemini",
        )
        self.assertEqual(packet["from_agent"], "gemini")


class TestDuplicatePublicationPrevention(unittest.TestCase):
    """Test duplicate publication detection."""

    def test_detects_duplicate(self):
        packets = (
            {
                "requested_action": "execute_publication",
                "approved_head_sha": "abc123",
            },
        )
        self.assertTrue(
            is_duplicate_publication(
                pending_packets=packets, approved_head_sha="abc123",
            )
        )

    def test_ignores_different_sha(self):
        packets = (
            {
                "requested_action": "execute_publication",
                "approved_head_sha": "abc123",
            },
        )
        self.assertFalse(
            is_duplicate_publication(
                pending_packets=packets, approved_head_sha="def456",
            )
        )

    def test_ignores_non_publication_packets(self):
        packets = (
            {
                "requested_action": "review_changes",
                "approved_head_sha": "abc123",
            },
        )
        self.assertFalse(
            is_duplicate_publication(
                pending_packets=packets, approved_head_sha="abc123",
            )
        )

    def test_empty_queue(self):
        self.assertFalse(
            is_duplicate_publication(
                pending_packets=(), approved_head_sha="abc123",
            )
        )


if __name__ == "__main__":
    unittest.main()
