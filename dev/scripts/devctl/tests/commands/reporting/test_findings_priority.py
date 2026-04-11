"""Tests for the findings-priority reporting command."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import COMMAND_HANDLERS, READ_ONLY_COMMANDS, build_parser
from dev.scripts.devctl.commands.listing import COMMANDS
from dev.scripts.devctl.commands.reporting import findings_priority as command
from dev.scripts.devctl.context_graph.models import EDGE_KIND_IMPORTS, GraphEdge, GraphNode, NODE_KIND_SOURCE
from dev.scripts.devctl.triage.findings_priority import (
    build_priority_payload,
    load_accumulated_findings,
    rank_accumulated_findings,
)


def _args(**overrides) -> SimpleNamespace:
    defaults = {
        "findings_file": "dev/audits/LIVE_RUN.md",
        "include_resolved": False,
        "top_n": 20,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _graph(*, paths: tuple[str, ...], outgoing_counts: dict[str, int]) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes = [
        GraphNode(
            node_id=f"src:{path}",
            node_kind=NODE_KIND_SOURCE,
            label=path,
            canonical_pointer_ref=path,
            provenance_ref="test",
            temperature=0.0,
            metadata={},
        )
        for path in paths
    ]
    edges: list[GraphEdge] = []
    for source_path, count in outgoing_counts.items():
        for index in range(count):
            target_path = paths[(index + 1) % len(paths)]
            edges.append(
                GraphEdge(
                    source_id=f"src:{source_path}",
                    target_id=f"src:{target_path}",
                    edge_kind=EDGE_KIND_IMPORTS,
                )
            )
    return nodes, edges


class FindingsPriorityParserTests(unittest.TestCase):
    def test_parser_accepts_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "findings-priority",
                "--findings-file",
                "/tmp/live-run.md",
                "--include-resolved",
                "--top-n",
                "5",
                "--format",
                "md",
            ]
        )
        self.assertEqual(args.command, "findings-priority")
        self.assertEqual(args.findings_file, "/tmp/live-run.md")
        self.assertTrue(args.include_resolved)
        self.assertEqual(args.top_n, 5)
        self.assertEqual(args.format, "md")

    def test_handler_and_listing_registered(self) -> None:
        self.assertIn("findings-priority", COMMAND_HANDLERS)
        self.assertIn("findings-priority", COMMANDS)
        self.assertIn("findings-priority", READ_ONLY_COMMANDS)


class FindingsPriorityRankingTests(unittest.TestCase):
    def test_ranking_prefers_severity_then_fan_out(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "LIVE_RUN.md"
            path.write_text(
                "\n".join(
                    [
                        "### Q2 — Medium priority drift",
                        "- **Severity**: medium",
                        "- **Location**: `pkg/medium.py`",
                        "- **Body**: medium fan-out finding",
                        "- **Status**: OPEN",
                        "",
                        "### Q3 — High fan-out issue",
                        "- **Severity**: behavioral, high",
                        "- **Location**: `pkg/high_fan.py`",
                        "- **Body**: high fan-out finding",
                        "- **Status**: OPEN",
                        "",
                        "### Q4 — High low-fan-out issue",
                        "- **Severity**: structural bug, high",
                        "- **Location**: `pkg/high_small.py`",
                        "- **Body**: lower fan-out finding",
                        "- **Status**: OPEN",
                    ]
                ),
                encoding="utf-8",
            )
            findings = load_accumulated_findings(path)
        nodes, edges = _graph(
            paths=("pkg/medium.py", "pkg/high_fan.py", "pkg/high_small.py"),
            outgoing_counts={
                "pkg/medium.py": 7,
                "pkg/high_fan.py": 5,
                "pkg/high_small.py": 1,
            },
        )
        ranked = rank_accumulated_findings(findings, graph_nodes=nodes, graph_edges=edges)
        self.assertEqual([row.qid for row in ranked], ["Q3", "Q4", "Q2"])
        self.assertEqual(ranked[0].max_fan_out, 5)
        self.assertEqual(ranked[1].max_fan_out, 1)

    def test_fixed_qid_supersedes_other_entries_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "LIVE_RUN.md"
            path.write_text(
                "\n".join(
                    [
                        "### Q1 — **FIXED** — historical note",
                        "- **Body**: fixed in commit abc123",
                        "",
                        "### Q1 — BUG — stale entry",
                        "- **Severity**: bug, load-bearing",
                        "- **Location**: `pkg/blocked.py`",
                        "- **Body**: old open entry",
                        "- **Status**: OPEN",
                        "",
                        "### Q2 — current issue",
                        "- **Severity**: medium",
                        "- **Location**: `pkg/open.py`",
                        "- **Body**: still open",
                        "- **Status**: OPEN",
                    ]
                ),
                encoding="utf-8",
            )
            findings = load_accumulated_findings(path)
        nodes, edges = _graph(
            paths=("pkg/blocked.py", "pkg/open.py"),
            outgoing_counts={"pkg/blocked.py": 4, "pkg/open.py": 1},
        )
        ranked = rank_accumulated_findings(findings, graph_nodes=nodes, graph_edges=edges)
        self.assertEqual([row.qid for row in ranked], ["Q2"])

    def test_payload_reports_resolution_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "LIVE_RUN.md"
            path.write_text(
                "\n".join(
                    [
                        "### Q7 — resolved note",
                        "- **Severity**: low",
                        "- **Body**: no action remains",
                        "- **Status**: FIXED",
                        "",
                        "### Q8 — open note",
                        "- **Severity**: push preflight friction, medium",
                        "- **Location**: `pkg/open.py`",
                        "- **Body**: action remains",
                        "- **Status**: STRUCTURAL FIX OPEN",
                    ]
                ),
                encoding="utf-8",
            )
            findings = load_accumulated_findings(path)
        nodes, edges = _graph(paths=("pkg/open.py",), outgoing_counts={"pkg/open.py": 2})
        ranked = rank_accumulated_findings(
            findings,
            graph_nodes=nodes,
            graph_edges=edges,
            include_resolved=True,
        )
        payload = build_priority_payload(
            source_path=path,
            findings=findings,
            ranked=ranked,
            include_resolved=True,
        )
        self.assertEqual(payload["summary"]["resolution_counts"]["open"], 1)
        self.assertEqual(payload["summary"]["resolution_counts"]["resolved"], 1)
        self.assertEqual(payload["summary"]["ranked_findings"], 2)


class FindingsPriorityCommandTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.reporting.findings_priority.write_output")
    @patch("dev.scripts.devctl.commands.reporting.findings_priority.build_context_graph")
    def test_run_emits_json_payload(
        self,
        build_context_graph_mock,
        write_output_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            findings_path = Path(tmp_dir) / "LIVE_RUN.md"
            findings_path.write_text(
                "\n".join(
                    [
                        "### Q9 — ranking target",
                        "- **Severity**: behavioral, high",
                        "- **Location**: `pkg/high.py`",
                        "- **Body**: current high priority issue",
                        "- **Status**: OPEN",
                    ]
                ),
                encoding="utf-8",
            )
            build_context_graph_mock.return_value = _graph(
                paths=("pkg/high.py",),
                outgoing_counts={"pkg/high.py": 3},
            )
            rc = command.run(_args(findings_file=str(findings_path)))

        self.assertEqual(rc, 0)
        output = write_output_mock.call_args.args[0]
        payload = json.loads(output)
        self.assertEqual(payload["command"], "findings-priority")
        self.assertEqual(payload["ranked_findings"][0]["qid"], "Q9")
        self.assertEqual(payload["ranked_findings"][0]["max_fan_out"], 3)
