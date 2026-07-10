"""Tests for bounded codeshape ingestion in the context graph."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.context_graph.builder import build_context_graph
from dev.scripts.devctl.context_graph.codeshape import build_codeshape_subgraph
from dev.scripts.devctl.context_graph.models import (
    EDGE_KIND_CALLS,
    NODE_KIND_FUNCTION,
    NODE_KIND_MUTATION_CALLSITE,
)


class CodeShapeSubgraphTests(unittest.TestCase):
    def test_collects_functions_calls_and_mutation_callsites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "pkg").mkdir()
            (repo_root / "pkg/helper.py").write_text(
                "\n".join(
                    [
                        "from pkg.runtime import run_git_capture",
                        "",
                        "def helper_commit():",
                        "    return run_git_capture(['commit', '-m', 'msg'])",
                    ]
                ),
                encoding="utf-8",
            )
            (repo_root / "pkg/runtime.py").write_text(
                "\n".join(
                    [
                        "def run_git_capture(args):",
                        "    return args",
                    ]
                ),
                encoding="utf-8",
            )
            (repo_root / "pkg/executor.py").write_text(
                "\n".join(
                    [
                        "from pkg.helper import helper_commit",
                        "",
                        "class GovernedVcsExecutor:",
                        "    def execute(self):",
                        "        return helper_commit()",
                    ]
                ),
                encoding="utf-8",
            )

            graph = build_codeshape_subgraph(
                repo_root=repo_root,
                scope_paths=(
                    "pkg/runtime.py",
                    "pkg/helper.py",
                    "pkg/executor.py",
                ),
            )

        kinds = {node.node_kind for node in graph.nodes}
        self.assertIn(NODE_KIND_FUNCTION, kinds)
        self.assertIn(NODE_KIND_MUTATION_CALLSITE, kinds)
        self.assertTrue(any(edge.edge_kind == EDGE_KIND_CALLS for edge in graph.edges))
        self.assertEqual(graph.parse_errors, ())

    def test_live_context_graph_includes_codeshape_nodes(self) -> None:
        nodes, _ = build_context_graph()
        kinds = {node.node_kind for node in nodes}
        self.assertIn(NODE_KIND_FUNCTION, kinds)
        self.assertIn(NODE_KIND_MUTATION_CALLSITE, kinds)
