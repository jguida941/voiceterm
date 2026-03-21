"""Focused tests for review-channel context packet injection surfaces."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ReviewChannelPromotionContextTests(unittest.TestCase):
    @patch("dev.scripts.devctl.review_channel.promotion.build_context_escalation_packet")
    def test_promotion_candidate_appends_context_packet(self, escalation_mock) -> None:
        from dev.scripts.devctl.context_graph.escalation import ContextEscalationPacket
        from dev.scripts.devctl.review_channel.promotion import (
            derive_promotion_candidate,
        )

        escalation_mock.return_value = ContextEscalationPacket(
            trigger="review-channel-promotion",
            query_terms=("MP-358",),
            matched_nodes=1,
            edge_count=1,
            canonical_refs=("dev/active/continuous_swarm.md",),
            evidence=("MP-358: nodes=1, edges=1",),
            markdown=(
                "## Context Recovery Packet\n\n"
                "- Trigger: `review-channel-promotion`"
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            plan_path = root / "dev/active/continuous_swarm.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(
                "\n".join(
                    [
                        "# Continuous Swarm",
                        "",
                        "## Execution Checklist",
                        "",
                        "### Phase 1 - Queue",
                        "- [ ] Implement automatic next-task promotion so the conductor keeps moving.",
                        "",
                        "## Progress Log",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            candidate = derive_promotion_candidate(
                repo_root=root,
                promotion_plan_path=plan_path,
                require_exists=True,
            )

        assert candidate is not None
        self.assertTrue(
            candidate.instruction.startswith(
                "- Next scoped plan item (dev/active/continuous_swarm.md):"
            )
        )
        self.assertIn("## Context Recovery Packet", candidate.instruction)
        self.assertIsNotNone(candidate.context_packet)


class ReviewChannelEventProjectionContextTests(unittest.TestCase):
    @patch(
        "dev.scripts.devctl.review_channel.event_projection.build_event_context_packet"
    )
    def test_event_queue_summary_carries_context_packet(self, packet_mock) -> None:
        from dev.scripts.devctl.context_graph.escalation import ContextEscalationPacket
        from dev.scripts.devctl.review_channel.event_projection import (
            build_event_queue_summary,
        )

        packet_mock.return_value = ContextEscalationPacket(
            trigger="review-channel-event",
            query_terms=("MP-355",),
            matched_nodes=2,
            edge_count=1,
            canonical_refs=("dev/active/review_channel.md",),
            evidence=("MP-355: nodes=2, edges=1",),
            markdown=(
                "## Context Recovery Packet\n\n"
                "- Trigger: `review-channel-event`"
            ),
        )

        summary = build_event_queue_summary(
            {"claude": 1},
            0,
            packets=[
                {
                    "packet_id": "rev_pkt_0001",
                    "status": "pending",
                    "summary": "review the live tranche",
                    "body": "Investigate MP-355 follow-up",
                    "plan_id": "MP-355",
                    "kind": "review",
                    "from_agent": "codex",
                    "to_agent": "claude",
                }
            ],
        )

        self.assertTrue(
            summary["derived_next_instruction"].startswith("review the live tranche")
        )
        self.assertIn(
            "## Context Recovery Packet",
            summary["derived_next_instruction"],
        )
        self.assertEqual(
            summary["derived_next_instruction_source"]["packet_id"],
            "rev_pkt_0001",
        )
        self.assertIn(
            "context_packet",
            summary["derived_next_instruction_source"],
        )
