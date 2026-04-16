"""Focused tests for review-channel context packet injection surfaces."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class ReviewChannelPromotionContextTests(unittest.TestCase):
    @patch("dev.scripts.devctl.review_channel.promotion.build_context_escalation_packet")
    def test_promotion_candidate_appends_bridge_safe_context_summary(
        self,
        escalation_mock,
    ) -> None:
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
        self.assertIn("- Context packet:", candidate.instruction)
        self.assertIn("- Canonical refs:", candidate.instruction)
        self.assertNotIn("## Context Recovery Packet", candidate.instruction)
        self.assertIsNotNone(candidate.context_packet)


class ReviewChannelEventProjectionContextTests(unittest.TestCase):
    @patch(
        "dev.scripts.devctl.review_channel.event_projection_context.build_context_escalation_packet"
    )
    @patch("dev.scripts.devctl.context_graph.snapshot_store.load_context_graph_snapshot")
    @patch("dev.scripts.devctl.config.get_repo_root")
    def test_event_context_packet_rehydrates_cached_snapshot_rows(
        self,
        repo_root_mock,
        load_snapshot_mock,
        escalation_mock,
    ) -> None:
        from dev.scripts.devctl.context_graph.models import GraphEdge, GraphNode
        from dev.scripts.devctl.review_channel.event_projection_context import (
            build_event_context_packet,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            snapshot_dir = root / "dev/reports/graph_snapshots"
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            (snapshot_dir / "latest.json").write_text("{}", encoding="utf-8")
            repo_root_mock.return_value = root
            load_snapshot_mock.return_value = SimpleNamespace(
                nodes=[
                    {
                        "node_id": "src:bridge",
                        "node_kind": "source_file",
                        "label": "bridge.md",
                        "canonical_pointer_ref": "bridge.md",
                        "provenance_ref": "snapshot",
                        "temperature": 0.6,
                        "metadata": {"scope": "bridge"},
                    }
                ],
                edges=[
                    {
                        "source_id": "plan:mp",
                        "target_id": "src:bridge",
                        "edge_kind": "documented_by",
                    }
                ],
            )

            build_event_context_packet(
                {
                    "summary": "Inspect bridge diff",
                    "body": "bridge.md changed",
                    "plan_id": "MP-999",
                    "kind": "finding",
                }
            )

        graph = escalation_mock.call_args.kwargs["graph"]
        self.assertIsInstance(graph[0][0], GraphNode)
        self.assertIsInstance(graph[1][0], GraphEdge)
        self.assertEqual(graph[0][0].metadata["scope"], "bridge")

    @patch(
        "dev.scripts.devctl.review_channel.event_projection.build_event_context_packet"
    )
    def test_event_queue_summary_carries_bridge_safe_context_summary(
        self,
        packet_mock,
    ) -> None:
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
            guidance_refs=("probe_design_smells@dev/active/review_channel.md:12",),
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
                    "kind": "instruction",
                    "from_agent": "codex",
                    "to_agent": "claude",
                }
            ],
        )

        self.assertTrue(
            summary["derived_next_instruction"].startswith("review the live tranche")
        )
        self.assertIn(
            "- Context packet:",
            summary["derived_next_instruction"],
        )
        self.assertNotIn(
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
        self.assertEqual(
            summary["derived_next_instruction_source"]["guidance_refs"],
            ["probe_design_smells@dev/active/review_channel.md:12"],
        )

    def test_action_request_priority_beats_newer_commentary(self) -> None:
        from dev.scripts.devctl.review_channel.event_projection import (
            build_event_queue_summary,
        )

        summary = build_event_queue_summary(
            {"codex": 2},
            0,
            packets=[
                {
                    "packet_id": "rev_pkt_instruction",
                    "status": "pending",
                    "summary": "Later commentary packet",
                    "body": "narrative update",
                    "plan_id": "MP-380",
                    "kind": "instruction",
                    "from_agent": "claude",
                    "to_agent": "codex",
                    "posted_at": "2026-04-11T22:40:00Z",
                    "expires_at_utc": "2999-01-01T00:00:00Z",
                },
                {
                    "packet_id": "rev_pkt_action",
                    "status": "pending",
                    "summary": "Execute the governed push",
                    "body": "push the reviewed slice",
                    "plan_id": "MP-380",
                    "kind": "action_request",
                    "from_agent": "claude",
                    "to_agent": "codex",
                    "requested_action": "push",
                    "posted_at": "2026-04-11T22:20:00Z",
                    "expires_at_utc": "2999-01-01T00:00:00Z",
                    "delivery_observed_at_utc": "2026-04-11T22:21:00Z",
                    "delivery_observed_by": "codex",
                    "execution_started_at_utc": "",
                    "execution_started_by": "",
                },
            ],
        )

        self.assertTrue(
            summary["derived_next_instruction"].startswith(
                "Priority action_request: Execute the governed push"
            )
        )
        self.assertEqual(
            summary["derived_next_instruction_source"]["packet_id"],
            "rev_pkt_action",
        )
        self.assertEqual(
            summary["derived_next_instruction_source"]["selection_policy"],
            "action_request_priority",
        )
        self.assertEqual(
            summary["derived_next_instruction_source"]["control_state"],
            "execution_pending",
        )
        self.assertTrue(summary["derived_next_instruction_source"]["wake_required"])
        self.assertEqual(
            summary["derived_next_instruction_source"]["requested_action"],
            "push",
        )

    @patch(
        "dev.scripts.devctl.review_channel.event_projection.build_event_context_packet"
    )
    def test_action_request_priority_skips_expensive_context_packet_build(
        self,
        packet_mock,
    ) -> None:
        from dev.scripts.devctl.review_channel.event_projection import (
            build_event_queue_summary,
        )

        summary = build_event_queue_summary(
            {"codex": 1},
            0,
            packets=[
                {
                    "packet_id": "rev_pkt_action",
                    "status": "pending",
                    "summary": "Execute the governed push",
                    "body": "push the reviewed slice",
                    "plan_id": "MP-380",
                    "kind": "action_request",
                    "from_agent": "claude",
                    "to_agent": "codex",
                    "requested_action": "push",
                    "posted_at": "2026-04-11T22:20:00Z",
                    "expires_at_utc": "2999-01-01T00:00:00Z",
                }
            ],
        )

        packet_mock.assert_not_called()
        self.assertTrue(
            summary["derived_next_instruction"].startswith(
                "Priority action_request: Execute the governed push"
            )
        )
        self.assertNotIn(
            "context_packet",
            summary["derived_next_instruction_source"],
        )

    def test_finding_packet_does_not_become_derived_next_instruction(self) -> None:
        from dev.scripts.devctl.review_channel.event_projection import (
            build_event_queue_summary,
        )

        summary = build_event_queue_summary(
            {"codex": 1},
            0,
            packets=[
                {
                    "packet_id": "rev_pkt_finding",
                    "status": "pending",
                    "summary": "Dashboard dogfood: 6 critical issues",
                    "body": "This is a finding, not the next instruction.",
                    "plan_id": "MP-380",
                    "kind": "finding",
                    "from_agent": "claude",
                    "to_agent": "codex",
                    "requested_action": "review_only",
                    "posted_at": "2026-04-11T22:40:00Z",
                    "expires_at_utc": "2999-01-01T00:00:00Z",
                }
            ],
        )

        self.assertEqual(summary["derived_next_instruction"], "")
        self.assertEqual(summary["derived_next_instruction_source"], {})
