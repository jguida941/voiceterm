"""Focused tests for context-graph snapshot-save behavior."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.context_graph.command import run
from dev.scripts.devctl.context_graph.models import BootstrapContext, GraphEdge, GraphNode, GraphSize
from dev.scripts.devctl.context_graph.snapshot import (
    CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID,
    CONTEXT_GRAPH_SNAPSHOT_SCHEMA_VERSION,
    ContextGraphSnapshotCapture,
    ContextGraphSnapshotReceipt,
    write_context_graph_snapshot,
)
from dev.scripts.devctl.context_graph.snapshot_store import (
    list_context_graph_snapshots,
    resolve_context_graph_snapshot_ref,
)


def _sample_nodes() -> list[GraphNode]:
    return [
        GraphNode(
            node_id="src:alpha.py",
            node_kind="source_file",
            label="alpha.py",
            canonical_pointer_ref="alpha.py",
            provenance_ref="test",
            temperature=0.2,
            metadata={"owner": "tests"},
        ),
        GraphNode(
            node_id="guard:code_shape",
            node_kind="guard",
            label="code_shape",
            canonical_pointer_ref="dev/scripts/checks/check_code_shape.py",
            provenance_ref="test",
            temperature=0.8,
            metadata={"severity": "high"},
        ),
    ]


def _sample_edges() -> list[GraphEdge]:
    return [
        GraphEdge(
            source_id="guard:code_shape",
            target_id="src:alpha.py",
            edge_kind="guards",
        )
    ]


class TestContextGraphSnapshotWriter(unittest.TestCase):
    """Verify the snapshot writer emits a typed full-graph artifact."""

    def test_write_context_graph_snapshot_persists_full_graph_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            receipt = write_context_graph_snapshot(
                _sample_nodes(),
                _sample_edges(),
                capture=ContextGraphSnapshotCapture(
                    source_mode="bootstrap",
                    repo_root=repo_root,
                    branch="feature/test",
                    commit_hash="abc123def456",
                    generated_at_utc="2026-03-22T16:00:00Z",
                    timestamp_slug="20260322T160000Z",
                ),
            )
            snapshot_path = repo_root / receipt.path
            self.assertTrue(snapshot_path.exists())
            payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["contract_id"], CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID)
            self.assertEqual(payload["schema_version"], CONTEXT_GRAPH_SNAPSHOT_SCHEMA_VERSION)
            self.assertEqual(payload["commit_hash"], "abc123def456")
            self.assertEqual(payload["branch"], "feature/test")
            self.assertEqual(payload["source_mode"], "bootstrap")
            self.assertEqual(payload["node_count"], 2)
            self.assertEqual(payload["edge_count"], 1)
            self.assertEqual(payload["nodes"][0]["metadata"]["owner"], "tests")
            self.assertEqual(payload["edges"][0]["edge_kind"], "guards")
            self.assertEqual(
                payload["temperature_distribution"]["buckets"]["0.00-0.24"],
                1,
            )
            self.assertEqual(
                payload["temperature_distribution"]["buckets"]["0.75-1.00"],
                1,
            )

    def test_snapshot_resolution_uses_capture_time_not_filesystem_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            first_receipt = write_context_graph_snapshot(
                _sample_nodes(),
                _sample_edges(),
                capture=ContextGraphSnapshotCapture(
                    source_mode="bootstrap",
                    repo_root=repo_root,
                    branch="feature/test",
                    commit_hash="111111111111",
                    generated_at_utc="2026-03-22T16:00:00Z",
                    timestamp_slug="20260322T160000Z",
                ),
            )
            second_receipt = write_context_graph_snapshot(
                _sample_nodes(),
                _sample_edges(),
                capture=ContextGraphSnapshotCapture(
                    source_mode="bootstrap",
                    repo_root=repo_root,
                    branch="feature/test",
                    commit_hash="222222222222",
                    generated_at_utc="2026-03-22T16:05:00Z",
                    timestamp_slug="20260322T160500Z",
                ),
            )
            first_path = repo_root / first_receipt.path
            second_path = repo_root / second_receipt.path
            second_stats = second_path.stat()
            os.utime(
                first_path,
                (second_stats.st_atime_ns / 1_000_000_000, second_stats.st_mtime_ns / 1_000_000_000 + 10),
            )

            ordered_paths = list_context_graph_snapshots(repo_root=repo_root)

            self.assertEqual([path.name for path in ordered_paths], [first_path.name, second_path.name])
            self.assertEqual(
                resolve_context_graph_snapshot_ref("latest", repo_root=repo_root),
                second_path.resolve(),
            )
            self.assertEqual(
                resolve_context_graph_snapshot_ref("previous", repo_root=repo_root),
                first_path.resolve(),
            )


class TestContextGraphSnapshotCommand(unittest.TestCase):
    """Verify command dispatch triggers snapshot-save in the right modes."""

    def test_bootstrap_mode_saves_snapshot_without_flag(self) -> None:
        args = SimpleNamespace(
            mode="bootstrap",
            save_snapshot=False,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            query="",
        )
        ctx = BootstrapContext(
            repo="codex-voice",
            branch="feature/test",
            bridge_active=False,
            graph_size=GraphSize(source_files=1, guards=1, probes=0, active_plans=1, edges=1),
            active_plans=[{"path": "dev/active/MASTER_PLAN.md", "role": "tracker", "scope": "MP-377"}],
            hotspots=[{"file": "alpha.py", "temperature": 0.2, "fan_in": 0, "fan_out": 0}],
            key_commands={},
            bootstrap_links={"execution_state": "dev/active/MASTER_PLAN.md"},
            push_enforcement={"recommended_action": "use_devctl_push"},
            usage="test",
        )
        receipt = ContextGraphSnapshotReceipt(
            path="dev/reports/graph_snapshots/abc.json",
            schema_version=1,
            contract_id=CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID,
            branch="feature/test",
            commit_hash="abc123",
            generated_at_utc="2026-03-22T16:00:00Z",
            source_mode="bootstrap",
            node_count=2,
            edge_count=1,
            temperature_distribution={"average": 0.5, "buckets": {}, "minimum": 0.2, "maximum": 0.8},
        )
        with (
            patch("dev.scripts.devctl.context_graph.command.build_context_graph", return_value=(_sample_nodes(), _sample_edges())),
            patch("dev.scripts.devctl.context_graph.command.build_bootstrap_context", return_value=ctx),
            patch("dev.scripts.devctl.context_graph.command.write_context_graph_snapshot", return_value=receipt) as write_snapshot,
            patch("dev.scripts.devctl.context_graph.command.emit_machine_artifact_output", return_value=0) as emit_output,
        ):
            result = run(args)
        self.assertEqual(result, 0)
        write_snapshot.assert_called_once()
        payload = emit_output.call_args.kwargs["json_payload"]
        self.assertEqual(payload["snapshot"]["path"], receipt.path)
        self.assertEqual(emit_output.call_args.kwargs["options"].summary["snapshot_path"], receipt.path)

    def test_query_mode_requires_explicit_snapshot_flag(self) -> None:
        args = SimpleNamespace(
            mode="query",
            save_snapshot=False,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            query="alpha",
        )
        with (
            patch("dev.scripts.devctl.context_graph.command.build_context_graph", return_value=(_sample_nodes(), _sample_edges())),
            patch("dev.scripts.devctl.context_graph.command.write_context_graph_snapshot") as write_snapshot,
            patch("dev.scripts.devctl.context_graph.command.emit_machine_artifact_output", return_value=0),
        ):
            result = run(args)
        self.assertEqual(result, 0)
        write_snapshot.assert_not_called()
