"""Tests for bounded context-graph escalation helpers."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.context_graph.escalation import (
    build_context_escalation_packet,
    collect_query_terms,
    extract_query_terms_from_text,
)
from dev.scripts.devctl.context_graph.models import GraphEdge, GraphNode


class ContextEscalationExtractionTests(unittest.TestCase):
    def test_extracts_mp_file_and_command_terms(self) -> None:
        terms = extract_query_terms_from_text(
            "Fix MP-377 after reading `dev/scripts/devctl/cli.py` and run "
            "`python3 dev/scripts/devctl.py check --profile ci`."
        )

        self.assertIn("MP-377", terms)
        self.assertIn("dev/scripts/devctl/cli.py", terms)
        self.assertIn("check", terms)

    def test_collect_terms_dedupes_across_inputs(self) -> None:
        terms = collect_query_terms(
            [
                "MP-377",
                {"summary": "Touch dev/scripts/devctl/cli.py"},
                ["MP-377", "python3 dev/scripts/devctl.py check --profile ci"],
            ],
            max_terms=4,
        )

        self.assertEqual(len(terms), len(set(terms)))
        self.assertIn("MP-377", terms)
        self.assertIn("dev/scripts/devctl/cli.py", terms)


class ContextEscalationPacketTests(unittest.TestCase):
    def test_packet_unions_multiple_queries(self) -> None:
        nodes = [
            GraphNode(
                node_id="plan:mp377",
                node_kind="active_plan",
                label="MP-377 plan",
                canonical_pointer_ref="dev/active/platform_authority_loop.md",
                provenance_ref="test",
                temperature=0.8,
                metadata={"scope": "MP-377"},
            ),
            GraphNode(
                node_id="src:cli",
                node_kind="source_file",
                label="dev/scripts/devctl/cli.py",
                canonical_pointer_ref="dev/scripts/devctl/cli.py",
                provenance_ref="test",
                temperature=0.6,
                metadata={},
            ),
        ]
        edges = [
            GraphEdge(
                source_id="plan:mp377",
                target_id="src:cli",
                edge_kind="documented_by",
            )
        ]

        packet = build_context_escalation_packet(
            trigger="unit-test",
            query_terms=("MP-377", "cli.py"),
            graph=(nodes, edges),
        )

        assert packet is not None
        self.assertEqual(packet.trigger, "unit-test")
        self.assertEqual(packet.query_terms, ("MP-377", "cli.py"))
        self.assertEqual(packet.matched_nodes, 2)
        self.assertEqual(packet.edge_count, 1)
        self.assertIn("dev/active/platform_authority_loop.md", packet.canonical_refs)
        self.assertIn("dev/scripts/devctl/cli.py", packet.canonical_refs)
        self.assertIn("Context Recovery Packet", packet.markdown)

    def test_packet_returns_none_when_no_terms(self) -> None:
        packet = build_context_escalation_packet(
            trigger="empty",
            query_terms=(),
            graph=([], []),
        )
        self.assertIsNone(packet)


if __name__ == "__main__":
    unittest.main()
