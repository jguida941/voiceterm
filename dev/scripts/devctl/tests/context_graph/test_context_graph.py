"""Tests for devctl context-graph query surface."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.context_graph.builder import build_context_graph
from dev.scripts.devctl.context_graph.query import (
    build_bootstrap_context,
    query_context_graph,
)
from dev.scripts.devctl.context_graph.concepts import build_concept_nodes
from dev.scripts.devctl.context_graph.models import (
    EDGE_KIND_CONTAINS,
    EDGE_KIND_IMPORTS,
    EDGE_KIND_RELATED_TO,
    EDGE_KIND_ROUTES_TO,
    NODE_KIND_CONCEPT,
    NODE_KIND_GUARD,
    NODE_KIND_PLAN,
    NODE_KIND_PROBE,
    NODE_KIND_SOURCE,
    HotIndexSummary,
    GraphEdge,
    GraphNode,
    QueryResult,
)
from dev.scripts.devctl.context_graph.render import render_query_result_markdown


def _make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "query": "",
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestContextGraphRegistration(unittest.TestCase):
    """Verify context-graph is wired into devctl CLI."""

    def test_parser_accepts_context_graph(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["context-graph", "--format", "md"])
        self.assertEqual(args.command, "context-graph")
        self.assertEqual(args.format, "md")

    def test_parser_accepts_query_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["context-graph", "--query", "code_shape"])
        self.assertEqual(args.query, "code_shape")

    def test_handler_registered(self) -> None:
        self.assertIn("context-graph", COMMAND_HANDLERS)


class TestContextGraphBuild(unittest.TestCase):
    """Verify graph builds from live repo artifacts."""

    def test_builds_without_error(self) -> None:
        nodes, edges = build_context_graph()
        self.assertGreater(len(nodes), 0)
        self.assertGreater(len(edges), 0)

    def test_contains_all_node_kinds(self) -> None:
        nodes, _ = build_context_graph()
        kinds = {n.node_kind for n in nodes}
        for expected in (NODE_KIND_SOURCE, NODE_KIND_PLAN, NODE_KIND_GUARD, NODE_KIND_PROBE):
            self.assertIn(expected, kinds, f"missing node kind: {expected}")

    def test_every_node_has_required_fields(self) -> None:
        nodes, _ = build_context_graph()
        for node in nodes[:100]:
            self.assertTrue(node.canonical_pointer_ref, f"{node.node_id} missing canonical_pointer_ref")
            self.assertTrue(node.provenance_ref, f"{node.node_id} missing provenance_ref")
            self.assertIsInstance(node.temperature, float)
            self.assertGreaterEqual(node.temperature, 0.0)
            self.assertLessEqual(node.temperature, 1.0)

    def test_no_worktree_paths_in_source_nodes(self) -> None:
        nodes, _ = build_context_graph()
        for node in nodes:
            if node.node_kind == NODE_KIND_SOURCE:
                self.assertNotIn(
                    ".claude/worktrees",
                    node.canonical_pointer_ref,
                    f"worktree path leaked into source nodes: {node.node_id}",
                )

    def test_no_worktree_paths_in_edges(self) -> None:
        _, edges = build_context_graph()
        for edge in edges:
            self.assertNotIn(".claude/worktrees", edge.source_id)
            self.assertNotIn(".claude/worktrees", edge.target_id)

    def test_bootstrap_active_plans_exclude_reference_docs(self) -> None:
        nodes, edges = build_context_graph()
        ctx = build_bootstrap_context(nodes, edges)
        for plan in ctx.active_plans:
            role = plan.get("role", "")
            self.assertIn(
                role, {"tracker", "spec"},
                f"bootstrap active_plans should only include tracker/spec, got role={role} for {plan.get('path')}",
            )

    def test_guard_nodes_route_to_source(self) -> None:
        nodes, edges = build_context_graph()
        guard_ids = {n.node_id for n in nodes if n.node_kind == NODE_KIND_GUARD}
        routes = [e for e in edges if e.edge_kind == EDGE_KIND_ROUTES_TO and e.source_id in guard_ids]
        self.assertGreater(len(routes), 0, "guard nodes should have routes_to edges to source files")


class TestContextGraphQuery(unittest.TestCase):
    """Verify query returns targeted subgraphs with evidence."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.nodes, cls.edges = build_context_graph()

    def test_empty_query_returns_hot_index(self) -> None:
        result = query_context_graph("", self.nodes, self.edges)
        self.assertEqual(len(result.matched_nodes), 20)
        self.assertGreater(result.hot_index_summary.total_nodes, 0)
        self.assertGreater(result.hot_index_summary.total_edges, 0)

    def test_file_path_query(self) -> None:
        result = query_context_graph("cli.py", self.nodes, self.edges)
        matched_refs = [n.canonical_pointer_ref for n in result.matched_nodes]
        self.assertTrue(
            any("cli.py" in ref for ref in matched_refs),
            "query for cli.py should match at least one cli.py file",
        )

    def test_mp_query_returns_plan_nodes(self) -> None:
        result = query_context_graph("MP-377", self.nodes, self.edges)
        plan_nodes = [n for n in result.matched_nodes if n.node_kind == NODE_KIND_PLAN]
        self.assertGreater(len(plan_nodes), 0, "MP-377 query should find plan nodes")

    def test_guard_query_returns_guard_and_source(self) -> None:
        result = query_context_graph("code_shape", self.nodes, self.edges)
        kinds = {n.node_kind for n in result.matched_nodes}
        self.assertIn(NODE_KIND_GUARD, kinds, "code_shape query should find guard nodes")

    def test_result_evidence_is_populated(self) -> None:
        result = query_context_graph("topology", self.nodes, self.edges)
        self.assertGreater(len(result.evidence), 0)

    def test_result_nodes_sorted_by_temperature(self) -> None:
        result = query_context_graph("check", self.nodes, self.edges)
        temps = [n.temperature for n in result.matched_nodes]
        self.assertEqual(temps, sorted(temps, reverse=True))


class TestContextGraphRender(unittest.TestCase):
    """Verify markdown rendering produces valid output."""

    def test_render_produces_markdown(self) -> None:
        nodes = [
            GraphNode(
                node_id="src:foo.py",
                node_kind=NODE_KIND_SOURCE,
                label="foo.py",
                canonical_pointer_ref="foo.py",
                provenance_ref="test",
                temperature=0.5,
            ),
        ]
        result = QueryResult(
            query="foo",
            matched_nodes=nodes,
            edges=[],
            hot_index_summary=HotIndexSummary(total_nodes=1, total_edges=0, nodes_by_kind={}, edges_by_kind={}),
            evidence=["matched 1 direct node(s)"],
        )
        md = render_query_result_markdown(result)
        self.assertIn("# Context Graph", md)
        self.assertIn("foo.py", md)
        self.assertIn("0.500", md)


class TestBootstrapContext(unittest.TestCase):
    """Verify bootstrap mode produces a usable startup packet."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.nodes, cls.edges = build_context_graph()

    def test_bootstrap_has_required_fields(self) -> None:
        ctx = build_bootstrap_context(self.nodes, self.edges)
        self.assertTrue(ctx.repo)
        self.assertTrue(ctx.branch)
        self.assertIsInstance(ctx.bridge_active, bool)
        self.assertIsNotNone(ctx.graph_size)
        self.assertIsNotNone(ctx.key_commands)
        self.assertIsNotNone(ctx.bootstrap_links)
        self.assertTrue(ctx.usage)

    def test_bootstrap_has_plans(self) -> None:
        ctx = build_bootstrap_context(self.nodes, self.edges)
        self.assertGreater(len(ctx.active_plans), 0)

    def test_bootstrap_has_hotspots(self) -> None:
        ctx = build_bootstrap_context(self.nodes, self.edges)
        self.assertGreater(len(ctx.hotspots), 0)
        for h in ctx.hotspots:
            self.assertIn("file", h)
            self.assertIn("temperature", h)

    def test_bootstrap_token_budget(self) -> None:
        """Bootstrap packet should stay under 5K tokens."""
        from dataclasses import asdict
        ctx = build_bootstrap_context(self.nodes, self.edges)
        size = len(json.dumps(asdict(ctx)))
        tokens = size // 4
        self.assertLess(tokens, 5000, f"bootstrap packet too large: {tokens} tokens")

    def test_parser_accepts_bootstrap_mode(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["context-graph", "--mode", "bootstrap"])
        self.assertEqual(args.mode, "bootstrap")


class TestConceptLayer(unittest.TestCase):
    """Verify ZGraph-compatible concept nodes are derived correctly."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.nodes, cls.edges = build_context_graph()

    def test_concept_nodes_exist(self) -> None:
        concepts = [n for n in self.nodes if n.node_kind == NODE_KIND_CONCEPT]
        self.assertGreater(len(concepts), 0, "should derive concept nodes from directory structure")

    def test_concept_has_contains_edges(self) -> None:
        contains = [e for e in self.edges if e.edge_kind == EDGE_KIND_CONTAINS]
        self.assertGreater(len(contains), 0, "concepts should have contains edges to member files")

    def test_concept_has_related_edges(self) -> None:
        related = [e for e in self.edges if e.edge_kind == EDGE_KIND_RELATED_TO]
        self.assertGreater(len(related), 0, "concepts with shared imports should have related_to edges")

    def test_concept_resolves_to_canonical_directory(self) -> None:
        concepts = [n for n in self.nodes if n.node_kind == NODE_KIND_CONCEPT]
        for c in concepts:
            self.assertTrue(c.canonical_pointer_ref, f"{c.node_id} missing canonical_pointer_ref")
            self.assertEqual(c.provenance_ref, "directory_structure")

    def test_concept_temperature_bounded(self) -> None:
        concepts = [n for n in self.nodes if n.node_kind == NODE_KIND_CONCEPT]
        for c in concepts:
            self.assertGreaterEqual(c.temperature, 0.0)
            self.assertLessEqual(c.temperature, 1.0)

    def test_worktree_paths_excluded(self) -> None:
        concepts = [n for n in self.nodes if n.node_kind == NODE_KIND_CONCEPT]
        for c in concepts:
            self.assertNotIn(".claude/worktrees", c.canonical_pointer_ref)

    def test_query_returns_concepts(self) -> None:
        result = query_context_graph("review_channel", self.nodes, self.edges)
        concept_nodes = [n for n in result.matched_nodes if n.node_kind == NODE_KIND_CONCEPT]
        self.assertGreater(len(concept_nodes), 0, "query should return concept nodes alongside source files")


class TestConceptRenderers(unittest.TestCase):
    """Verify mermaid and dot renderers produce valid output with canonical refs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.nodes, cls.edges = build_context_graph()

    def test_mermaid_renders_concept_nodes(self) -> None:
        from dev.scripts.devctl.context_graph.render import render_concept_mermaid
        output = render_concept_mermaid(self.nodes, self.edges)
        self.assertIn("graph LR", output)
        self.assertIn("files, temp", output)

    def test_dot_renders_concept_nodes(self) -> None:
        from dev.scripts.devctl.context_graph.render import render_concept_dot
        output = render_concept_dot(self.nodes, self.edges)
        self.assertIn("digraph ConceptGraph", output)
        self.assertIn('rankdir="LR"', output)

    def test_mermaid_has_no_worktree_refs(self) -> None:
        from dev.scripts.devctl.context_graph.render import render_concept_mermaid
        output = render_concept_mermaid(self.nodes, self.edges)
        self.assertNotIn(".claude/worktrees", output)

    def test_documented_by_edges_in_mermaid(self) -> None:
        from dev.scripts.devctl.context_graph.render import render_concept_mermaid
        output = render_concept_mermaid(self.nodes, self.edges)
        # documented_by edges render as dotted arrows
        self.assertIn("-.->", output)


class TestGraphHonesty(unittest.TestCase):
    """Verify the three graph honesty fixes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.nodes, cls.edges = build_context_graph()

    def test_bootstrap_commands_from_policy(self) -> None:
        ctx = build_bootstrap_context(self.nodes, self.edges)
        self.assertGreater(len(ctx.key_commands), 0, "commands should load from governance policy")

    def test_bootstrap_links_from_policy(self) -> None:
        ctx = build_bootstrap_context(self.nodes, self.edges)
        self.assertIn("sdlc_policy", ctx.bootstrap_links)
        self.assertIn("execution_state", ctx.bootstrap_links)

    def test_plan_documented_by_edges_exist(self) -> None:
        from dev.scripts.devctl.context_graph.models import EDGE_KIND_DOCUMENTED_BY
        doc_edges = [e for e in self.edges if e.edge_kind == EDGE_KIND_DOCUMENTED_BY]
        self.assertGreater(len(doc_edges), 0, "plans should have documented_by edges to concepts")

    def test_mp377_query_has_connected_edges(self) -> None:
        result = query_context_graph("MP-377", self.nodes, self.edges)
        self.assertGreater(len(result.edges), 0, "MP-377 query should return connected edges")
        plan_nodes = [n for n in result.matched_nodes if n.node_kind == NODE_KIND_PLAN]
        self.assertGreater(len(plan_nodes), 0, "MP-377 query should find plan nodes")

    def test_scope_text_is_clean(self) -> None:
        plan_nodes = [n for n in self.nodes if n.node_kind == NODE_KIND_PLAN]
        for p in plan_nodes:
            scope = str(p.metadata.get("scope", ""))
            self.assertNotIn("`", scope, f"scope has markdown backticks: {p.node_id}")


class TestModeFormatDispatch(unittest.TestCase):
    """Verify mode/format dispatch contract (M5/M6)."""

    def test_concept_view_mode_accepted(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["context-graph", "--mode", "concept-view", "--format", "mermaid"])
        self.assertEqual(args.mode, "concept-view")

    def test_context_graph_in_devctl_list(self) -> None:
        from dev.scripts.devctl.commands.listing import COMMANDS
        self.assertIn("context-graph", COMMANDS)


if __name__ == "__main__":
    unittest.main()
