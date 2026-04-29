"""Tests for devctl graph-walk navigation."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.cli import COMMAND_HANDLERS, READ_ONLY_COMMANDS, build_parser
from dev.scripts.devctl.context_graph.graph_walk import walk_context_graph
from dev.scripts.devctl.context_graph.models import (
    EDGE_KIND_COMMAND_INVOKES,
    EDGE_KIND_DOCUMENTED_BY,
    EDGE_KIND_GUARD_CATCHES,
    EDGE_KIND_PACKET_HANDOFF,
    EDGE_KIND_ROUTES_TO,
    NODE_KIND_CAPABILITY,
    NODE_KIND_COMMAND,
    NODE_KIND_CONCEPT,
    NODE_KIND_FINDING,
    NODE_KIND_GUARD,
    NODE_KIND_PACKET,
    NODE_KIND_PLAN,
    GraphEdge,
    GraphNode,
)


def _node(node_id: str, kind: str, label: str) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        node_kind=kind,
        label=label,
        canonical_pointer_ref=label,
        provenance_ref="test",
        temperature=0.1,
        metadata={"aliases": [label]},
    )


class TestGraphWalkRegistration(unittest.TestCase):
    """Verify graph-walk is a first-class read-only devctl command."""

    def test_parser_accepts_graph_walk(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["graph-walk", "--from", "packet:rev_pkt_1", "--to", "command"])
        self.assertEqual(args.command, "graph-walk")
        self.assertEqual(args.from_node, "packet:rev_pkt_1")
        self.assertEqual(args.to_node, "command")

    def test_handler_registered(self) -> None:
        self.assertIn("graph-walk", COMMAND_HANDLERS)

    def test_graph_walk_is_read_only(self) -> None:
        self.assertIn("graph-walk", READ_ONLY_COMMANDS)


class TestGraphWalkTraversal(unittest.TestCase):
    """Verify deterministic path selection and confidence semantics."""

    def test_walk_packet_to_command_kind(self) -> None:
        nodes = [
            _node("packet:rev_pkt_1", NODE_KIND_PACKET, "rev_pkt_1"),
            _node("agent:claude", NODE_KIND_CAPABILITY, "claude"),
            _node("cmd:commit", NODE_KIND_COMMAND, "commit"),
        ]
        edges = [
            GraphEdge("packet:rev_pkt_1", "agent:claude", EDGE_KIND_PACKET_HANDOFF),
            GraphEdge("packet:rev_pkt_1", "cmd:commit", EDGE_KIND_ROUTES_TO),
        ]

        result = walk_context_graph("packet:rev_pkt_1", "command", nodes, edges)

        self.assertEqual(result.confidence, "high")
        self.assertEqual(result.path[-1].node_id, "cmd:commit")
        self.assertEqual(result.path[-1].inbound_edge_kind, EDGE_KIND_ROUTES_TO)

    def test_walk_follows_multi_hop_typed_edges(self) -> None:
        nodes = [
            _node("packet:rev_pkt_1", NODE_KIND_PACKET, "rev_pkt_1"),
            _node("cmd:check", NODE_KIND_COMMAND, "check"),
            _node("guard:code_shape", NODE_KIND_GUARD, "code_shape"),
            _node("finding:f1", NODE_KIND_FINDING, "f1"),
        ]
        edges = [
            GraphEdge("packet:rev_pkt_1", "cmd:check", EDGE_KIND_ROUTES_TO),
            GraphEdge("cmd:check", "guard:code_shape", EDGE_KIND_COMMAND_INVOKES),
            GraphEdge("guard:code_shape", "finding:f1", EDGE_KIND_GUARD_CATCHES),
        ]

        result = walk_context_graph("rev_pkt_1", "finding", nodes, edges)

        self.assertEqual(result.confidence, "high")
        self.assertEqual([step.node_id for step in result.path], [
            "packet:rev_pkt_1",
            "cmd:check",
            "guard:code_shape",
            "finding:f1",
        ])

    def test_heuristic_only_path_is_low_confidence(self) -> None:
        nodes = [
            _node("plan:dev/active/test.md", NODE_KIND_PLAN, "dev/active/test.md"),
            _node("concept:dev/scripts/devctl", NODE_KIND_CONCEPT, "dev/scripts/devctl"),
        ]
        edges = [
            GraphEdge(
                "plan:dev/active/test.md",
                "concept:dev/scripts/devctl",
                EDGE_KIND_DOCUMENTED_BY,
            )
        ]

        result = walk_context_graph("test.md", "concept", nodes, edges)

        self.assertEqual(result.confidence, "low_confidence")
        self.assertEqual(result.path[-1].node_id, "concept:dev/scripts/devctl")

    def test_no_match_when_start_missing(self) -> None:
        nodes = [_node("cmd:check", NODE_KIND_COMMAND, "check")]

        result = walk_context_graph("missing", "command", nodes, [])

        self.assertEqual(result.confidence, "no_match")
        self.assertFalse(result.path)


if __name__ == "__main__":
    unittest.main()
