"""Focused tests for saved context-graph snapshot diff/trend behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.context_graph.command import run
from dev.scripts.devctl.context_graph.models import GraphEdge, GraphNode
from dev.scripts.devctl.context_graph.snapshot import (
    ContextGraphSnapshotCapture,
    SnapshotResolutionError,
    write_context_graph_snapshot,
)
from dev.scripts.devctl.context_graph.snapshot_diff import (
    build_snapshot_trend,
    compute_graph_delta,
    load_graph_delta,
)
from dev.scripts.devctl.context_graph.snapshot_diff_render import render_snapshot_delta_markdown
from dev.scripts.devctl.context_graph.snapshot_store import load_context_graph_snapshot


def _write_snapshot(
    repo_root: Path,
    *,
    commit_hash: str,
    timestamp_slug: str,
    generated_at_utc: str,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> Path:
    receipt = write_context_graph_snapshot(
        nodes,
        edges,
        capture=ContextGraphSnapshotCapture(
            source_mode="bootstrap",
            repo_root=repo_root,
            branch="feature/test",
            commit_hash=commit_hash,
            generated_at_utc=generated_at_utc,
            timestamp_slug=timestamp_slug,
        ),
    )
    return repo_root / receipt.path


def _base_nodes() -> list[GraphNode]:
    return [
        GraphNode(
            node_id="src:a.py",
            node_kind="source_file",
            label="a.py",
            canonical_pointer_ref="a.py",
            provenance_ref="test",
            temperature=0.10,
            metadata={},
        ),
        GraphNode(
            node_id="src:b.py",
            node_kind="source_file",
            label="b.py",
            canonical_pointer_ref="b.py",
            provenance_ref="test",
            temperature=0.20,
            metadata={},
        ),
    ]


def _base_edges() -> list[GraphEdge]:
    return [
        GraphEdge(
            source_id="src:a.py",
            target_id="src:b.py",
            edge_kind="imports",
        )
    ]


class TestContextGraphSnapshotLoad(unittest.TestCase):
    """Verify saved snapshots round-trip into the typed contract."""

    def test_load_context_graph_snapshot_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            snapshot_path = _write_snapshot(
                repo_root,
                commit_hash="111111111111",
                timestamp_slug="20260323T040000Z",
                generated_at_utc="2026-03-23T04:00:00Z",
                nodes=_base_nodes(),
                edges=_base_edges(),
            )
            snapshot = load_context_graph_snapshot(snapshot_path)
            self.assertEqual(snapshot.commit_hash, "111111111111")
            self.assertEqual(snapshot.node_count, 2)
            self.assertEqual(snapshot.edge_count, 1)
            self.assertEqual(snapshot.temperature_distribution.buckets["0.00-0.24"], 2)


class TestContextGraphSnapshotDelta(unittest.TestCase):
    """Verify delta/trend summaries over saved snapshots."""

    def test_compute_graph_delta_detects_node_edge_and_temperature_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            before_path = _write_snapshot(
                repo_root,
                commit_hash="111111111111",
                timestamp_slug="20260323T040000Z",
                generated_at_utc="2026-03-23T04:00:00Z",
                nodes=_base_nodes(),
                edges=_base_edges(),
            )
            after_nodes = _base_nodes() + [
                GraphNode(
                    node_id="src:c.py",
                    node_kind="source_file",
                    label="c.py",
                    canonical_pointer_ref="c.py",
                    provenance_ref="test",
                    temperature=0.85,
                    metadata={},
                )
            ]
            after_nodes[0] = GraphNode(
                node_id="src:a.py",
                node_kind="source_file",
                label="a.py",
                canonical_pointer_ref="a.py",
                provenance_ref="test",
                temperature=0.65,
                metadata={},
            )
            after_edges = [
                GraphEdge(source_id="src:a.py", target_id="src:b.py", edge_kind="imports"),
                GraphEdge(source_id="src:b.py", target_id="src:a.py", edge_kind="imports"),
                GraphEdge(source_id="src:c.py", target_id="src:a.py", edge_kind="guards"),
            ]
            after_path = _write_snapshot(
                repo_root,
                commit_hash="222222222222",
                timestamp_slug="20260323T040500Z",
                generated_at_utc="2026-03-23T04:05:00Z",
                nodes=after_nodes,
                edges=after_edges,
            )
            delta = compute_graph_delta(
                load_context_graph_snapshot(before_path),
                load_context_graph_snapshot(after_path),
                from_path=before_path,
                to_path=after_path,
                trend=None,
            )
            self.assertEqual(delta.added_nodes_count, 1)
            self.assertEqual(delta.added_edges_count, 2)
            self.assertIn("guards", delta.new_edge_kinds)
            self.assertEqual(delta.changed_nodes_count, 1)
            self.assertEqual(delta.hottest_increases[0].node_id, "src:a.py")
            self.assertEqual(delta.to_snapshot.import_cycle_count, 1)

    def test_build_snapshot_trend_reports_hotter_direction_and_cycle_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            first_path = _write_snapshot(
                repo_root,
                commit_hash="111111111111",
                timestamp_slug="20260323T040000Z",
                generated_at_utc="2026-03-23T04:00:00Z",
                nodes=_base_nodes(),
                edges=_base_edges(),
            )
            second_nodes = [
                GraphNode(
                    node_id="src:a.py",
                    node_kind="source_file",
                    label="a.py",
                    canonical_pointer_ref="a.py",
                    provenance_ref="test",
                    temperature=0.75,
                    metadata={},
                ),
                GraphNode(
                    node_id="src:b.py",
                    node_kind="source_file",
                    label="b.py",
                    canonical_pointer_ref="b.py",
                    provenance_ref="test",
                    temperature=0.80,
                    metadata={},
                ),
            ]
            second_edges = [
                GraphEdge(source_id="src:a.py", target_id="src:b.py", edge_kind="imports"),
                GraphEdge(source_id="src:b.py", target_id="src:a.py", edge_kind="imports"),
            ]
            second_path = _write_snapshot(
                repo_root,
                commit_hash="222222222222",
                timestamp_slug="20260323T041000Z",
                generated_at_utc="2026-03-23T04:10:00Z",
                nodes=second_nodes,
                edges=second_edges,
            )
            with patch(
                "dev.scripts.devctl.context_graph.snapshot_store.list_context_graph_snapshots",
                return_value=[first_path, second_path],
            ):
                trend = build_snapshot_trend(to_path=second_path, window_size=5)
            self.assertIsNotNone(trend)
            assert trend is not None
            self.assertEqual(trend.temperature_direction, "hotter")
            self.assertGreater(trend.average_temperature_delta, 0.0)
            self.assertEqual(trend.import_cycle_delta, 1)

    def test_render_snapshot_delta_markdown_surfaces_removed_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            before_path = _write_snapshot(
                repo_root,
                commit_hash="111111111111",
                timestamp_slug="20260323T040000Z",
                generated_at_utc="2026-03-23T04:00:00Z",
                nodes=_base_nodes(),
                edges=_base_edges(),
            )
            after_nodes = [_base_nodes()[0]]
            after_path = _write_snapshot(
                repo_root,
                commit_hash="222222222222",
                timestamp_slug="20260323T041000Z",
                generated_at_utc="2026-03-23T04:10:00Z",
                nodes=after_nodes,
                edges=[],
            )
            delta = compute_graph_delta(
                load_context_graph_snapshot(before_path),
                load_context_graph_snapshot(after_path),
                from_path=before_path,
                to_path=after_path,
                trend=None,
            )
            rendered = render_snapshot_delta_markdown(delta)
            self.assertIn("## Removed Nodes", rendered)
            self.assertIn("## Removed Edges", rendered)

    def test_load_graph_delta_rejects_identical_snapshot_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            snapshot_path = _write_snapshot(
                repo_root,
                commit_hash="111111111111",
                timestamp_slug="20260323T040000Z",
                generated_at_utc="2026-03-23T04:00:00Z",
                nodes=_base_nodes(),
                edges=_base_edges(),
            )
            with patch(
                "dev.scripts.devctl.context_graph.snapshot.get_repo_root",
                return_value=repo_root,
            ):
                with self.assertRaises(SnapshotResolutionError):
                    load_graph_delta(
                        from_ref=str(snapshot_path),
                        to_ref=str(snapshot_path),
                        trend_window=5,
                    )

    def test_load_graph_delta_ignores_non_snapshot_json_neighbors_for_direct_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            mixed_dir = repo_root / "mixed"
            mixed_dir.mkdir()
            before_path = _write_snapshot(
                repo_root,
                commit_hash="111111111111",
                timestamp_slug="20260323T040000Z",
                generated_at_utc="2026-03-23T04:00:00Z",
                nodes=_base_nodes(),
                edges=_base_edges(),
            )
            after_path = _write_snapshot(
                repo_root,
                commit_hash="222222222222",
                timestamp_slug="20260323T041000Z",
                generated_at_utc="2026-03-23T04:10:00Z",
                nodes=_base_nodes(),
                edges=_base_edges(),
            )
            moved_before = mixed_dir / before_path.name
            moved_after = mixed_dir / after_path.name
            before_path.replace(moved_before)
            after_path.replace(moved_after)
            (mixed_dir / "junk.json").write_text('{"hello": "world"}\n', encoding="utf-8")

            delta = load_graph_delta(
                from_ref=str(moved_before),
                to_ref=str(moved_after),
                trend_window=5,
            )

            self.assertIsNotNone(delta.trend)
            assert delta.trend is not None
            self.assertEqual(delta.trend.window_size, 2)
            self.assertEqual(delta.to_snapshot.path, moved_after.name)


class TestContextGraphDiffCommand(unittest.TestCase):
    """Verify diff mode emits the typed delta payload through the command path."""

    def test_run_diff_mode_uses_saved_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            before_path = _write_snapshot(
                repo_root,
                commit_hash="111111111111",
                timestamp_slug="20260323T040000Z",
                generated_at_utc="2026-03-23T04:00:00Z",
                nodes=_base_nodes(),
                edges=_base_edges(),
            )
            after_nodes = _base_nodes()
            after_nodes[0] = GraphNode(
                node_id="src:a.py",
                node_kind="source_file",
                label="a.py",
                canonical_pointer_ref="a.py",
                provenance_ref="test",
                temperature=0.55,
                metadata={},
            )
            after_path = _write_snapshot(
                repo_root,
                commit_hash="222222222222",
                timestamp_slug="20260323T041000Z",
                generated_at_utc="2026-03-23T04:10:00Z",
                nodes=after_nodes,
                edges=_base_edges(),
            )
            args = SimpleNamespace(
                mode="diff",
                from_snapshot=str(before_path),
                to_snapshot=str(after_path),
                trend_window=5,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
            )
            with (
                patch(
                    "dev.scripts.devctl.context_graph.snapshot_store.list_context_graph_snapshots",
                    return_value=[before_path, after_path],
                ),
                patch("dev.scripts.devctl.context_graph.command.emit_machine_artifact_output", return_value=0) as emit_output,
            ):
                result = run(args)
            self.assertEqual(result, 0)
            payload = emit_output.call_args.kwargs["json_payload"]
            self.assertEqual(payload["contract_id"], "ContextGraphDelta")
            self.assertEqual(payload["from_snapshot"]["commit_hash"], "111111111111")
            self.assertEqual(payload["to_snapshot"]["commit_hash"], "222222222222")
            self.assertEqual(payload["changed_nodes_count"], 1)
            self.assertEqual(
                payload["from_snapshot"]["path"],
                "dev/reports/graph_snapshots/111111111111_20260323T040000Z.json",
            )
            self.assertEqual(
                payload["to_snapshot"]["path"],
                "dev/reports/graph_snapshots/222222222222_20260323T041000Z.json",
            )
