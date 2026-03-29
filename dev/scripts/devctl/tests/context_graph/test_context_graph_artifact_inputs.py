"""Regression tests for context-graph artifact inputs and topology scanning."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.context_graph.artifact_inputs import load_artifact_inputs
from dev.scripts.devctl.probe_topology_scan import iter_source_files


def _topology_payload(*, generated_at: str | None) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_id": "FileTopology",
        "summary": {},
        "nodes": {
            "dev/scripts/devctl/context_graph/builder.py": {
                "hint_count": 2,
                "changed": True,
            },
            "dev/scripts/devctl/context_graph/command.py": {
                "hint_count": 0,
                "changed": False,
            },
        },
        "edges": [],
        "hotspots": [],
        "focused_graph": {"nodes": [], "edges": []},
        "warnings": [],
    }
    if generated_at is not None:
        payload["generated_at"] = generated_at
    return payload


def _write_topology(repo_root: Path, payload: dict[str, object]) -> None:
    topology_path = repo_root / "dev" / "reports" / "probes" / "latest" / "file_topology.json"
    topology_path.parent.mkdir(parents=True, exist_ok=True)
    topology_path.write_text(json.dumps(payload), encoding="utf-8")


def _write_summary(repo_root: Path, *, generated_at: str | None) -> None:
    """Write a summary.json with the probe-run timestamp (the sibling artifact
    that carries generated_at for freshness gating)."""
    summary_path = repo_root / "dev" / "reports" / "probes" / "latest" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {"schema_version": 1, "contract_id": "ProbeReport"}
    if generated_at is not None:
        payload["generated_at"] = generated_at
    summary_path.write_text(json.dumps(payload), encoding="utf-8")


def _utc_timestamp(delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    if delta is not None:
        now += delta
    return now.isoformat().replace("+00:00", "Z")


class TestContextGraphArtifactInputs(unittest.TestCase):
    def test_missing_generated_at_falls_back_to_empty_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))
            # No summary.json → no timestamp → stale

            hint_counts, changed_paths, _severity = load_artifact_inputs(repo_root)

        self.assertEqual(hint_counts, {})
        self.assertEqual(changed_paths, set())

    def test_stale_generated_at_falls_back_to_empty_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))
            _write_summary(repo_root, generated_at=_utc_timestamp(delta=timedelta(hours=-7)))

            hint_counts, changed_paths, _severity = load_artifact_inputs(repo_root)

        self.assertEqual(hint_counts, {})
        self.assertEqual(changed_paths, set())

    def test_fresh_generated_at_loads_hint_counts_and_changed_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))
            _write_summary(repo_root, generated_at=_utc_timestamp())

            hint_counts, changed_paths, _severity = load_artifact_inputs(repo_root)

        self.assertEqual(
            hint_counts,
            {"dev/scripts/devctl/context_graph/builder.py": 2},
        )
        self.assertEqual(
            changed_paths,
            {"dev/scripts/devctl/context_graph/builder.py"},
        )


class TestSeverityFromReviewPacket(unittest.TestCase):
    """Verify severity is loaded from review_packet.json hotspots, not topology nodes."""

    def test_severity_loaded_from_review_packet_hotspots(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))
            _write_summary(repo_root, generated_at=_utc_timestamp())
            # Write review_packet with severity in hotspots (no generated_at — contract doesn't emit it)
            packet_path = repo_root / "dev" / "reports" / "probes" / "latest" / "review_packet.json"
            packet_payload = {
                "schema_version": 1,
                "contract_id": "ReviewPacket",
                "hotspots": [
                    {
                        "file": "dev/scripts/devctl/context_graph/builder.py",
                        "severity_counts": {"high": 3, "medium": 2},
                    },
                ],
            }
            packet_path.write_text(json.dumps(packet_payload), encoding="utf-8")

            _hints, _changed, severity = load_artifact_inputs(repo_root)

        self.assertEqual(
            severity,
            {"dev/scripts/devctl/context_graph/builder.py": "high"},
        )

    def test_severity_empty_when_no_review_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))
            _write_summary(repo_root, generated_at=_utc_timestamp())
            # No review_packet.json

            _hints, _changed, severity = load_artifact_inputs(repo_root)

        self.assertEqual(severity, {})

    def test_severity_empty_when_probe_run_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))
            _write_summary(repo_root, generated_at=_utc_timestamp(delta=timedelta(hours=-7)))
            packet_path = repo_root / "dev" / "reports" / "probes" / "latest" / "review_packet.json"
            packet_payload = {
                "schema_version": 1,
                "contract_id": "ReviewPacket",
                "hotspots": [{"file": "a.py", "severity_counts": {"high": 1}}],
            }
            packet_path.write_text(json.dumps(packet_payload), encoding="utf-8")

            _hints, _changed, severity = load_artifact_inputs(repo_root)

        self.assertEqual(severity, {})


class TestResolveGraphInputsPartialMerge(unittest.TestCase):
    """Verify resolve_graph_inputs preserves explicit empty inputs."""

    def test_explicit_empty_hint_counts_preserved(self) -> None:
        from dev.scripts.devctl.context_graph.artifact_inputs import resolve_graph_inputs

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))
            _write_summary(repo_root, generated_at=_utc_timestamp())

            # Explicit empty dict — should NOT be overwritten by artifact
            hints, changed, _sev = resolve_graph_inputs(
                repo_root, hint_counts={}, changed_paths=None
            )

        self.assertEqual(hints, {})  # Preserved explicit empty
        # changed_paths should be filled from artifact
        self.assertEqual(changed, {"dev/scripts/devctl/context_graph/builder.py"})

    def test_explicit_empty_changed_paths_preserved(self) -> None:
        from dev.scripts.devctl.context_graph.artifact_inputs import resolve_graph_inputs

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))
            _write_summary(repo_root, generated_at=_utc_timestamp())

            hints, changed, _sev = resolve_graph_inputs(
                repo_root, hint_counts=None, changed_paths=set()
            )

        # hint_counts should be filled from artifact
        self.assertEqual(hints, {"dev/scripts/devctl/context_graph/builder.py": 2})
        self.assertEqual(changed, set())  # Preserved explicit empty

    def test_both_none_fills_from_artifact(self) -> None:
        from dev.scripts.devctl.context_graph.artifact_inputs import resolve_graph_inputs

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))
            _write_summary(repo_root, generated_at=_utc_timestamp())

            hints, changed, _sev = resolve_graph_inputs(
                repo_root, hint_counts=None, changed_paths=None
            )

        self.assertEqual(hints, {"dev/scripts/devctl/context_graph/builder.py": 2})
        self.assertEqual(changed, {"dev/scripts/devctl/context_graph/builder.py"})

    def test_both_explicit_skips_artifact_for_hints_and_changed(self) -> None:
        from dev.scripts.devctl.context_graph.artifact_inputs import resolve_graph_inputs

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))
            _write_summary(repo_root, generated_at=_utc_timestamp())

            hints, changed, _sev = resolve_graph_inputs(
                repo_root, hint_counts={"custom.py": 5}, changed_paths={"custom.py"}
            )

        self.assertEqual(hints, {"custom.py": 5})
        self.assertEqual(changed, {"custom.py"})


class TestProbeTopologyScanExclusions(unittest.TestCase):
    def test_path_specific_exclusions_do_not_blacklist_same_basename_elsewhere(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            included_paths = (
                repo_root / "src" / "keep.rs",
                repo_root / "nested" / "worktrees" / "keep.py",
                repo_root / "nested" / "repo_example_temp" / "keep.py",
            )
            excluded_paths = (
                repo_root / ".claude" / "worktrees" / "ignored.py",
                repo_root / "dev" / "repo_example_temp" / "ignored.py",
            )
            for path in (*included_paths, *excluded_paths):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("pass\n", encoding="utf-8")

            with patch("dev.scripts.devctl.probe_topology.source_paths.get_repo_root", return_value=repo_root):
                buckets = iter_source_files()

        python_paths = {path.relative_to(repo_root).as_posix() for path in buckets["python"]}
        rust_paths = {path.relative_to(repo_root).as_posix() for path in buckets["rust"]}
        self.assertEqual(rust_paths, {"src/keep.rs"})
        self.assertIn("nested/worktrees/keep.py", python_paths)
        self.assertIn("nested/repo_example_temp/keep.py", python_paths)
        self.assertNotIn(".claude/worktrees/ignored.py", python_paths)
        self.assertNotIn("dev/repo_example_temp/ignored.py", python_paths)


class TestBuilderSeverityReachesSourceNode(unittest.TestCase):
    """End-to-end: prove severity from review_packet.json hotspots reaches
    built source-node metadata and temperature via build_context_graph()."""

    def test_build_context_graph_threads_severity_into_source_node(self) -> None:
        """Build a real graph from temp artifacts and verify the source node
        carries severity metadata and a boosted temperature."""
        from dev.scripts.devctl.context_graph.builder import build_context_graph

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Create a minimal Python source file so the topology scan finds it
            src_dir = repo_root / "dev" / "scripts"
            src_dir.mkdir(parents=True)
            src_file = src_dir / "example.py"
            src_file.write_text("pass\n", encoding="utf-8")

            # Write topology with the source file as a node (hint_count=3, changed=True)
            _write_topology(repo_root, {
                "schema_version": 1,
                "contract_id": "FileTopology",
                "summary": {},
                "nodes": {
                    "dev/scripts/example.py": {
                        "hint_count": 3,
                        "changed": True,
                    },
                },
                "edges": [],
                "hotspots": [],
                "focused_graph": {"nodes": [], "edges": []},
                "warnings": [],
            })

            # Write summary.json with fresh timestamp
            _write_summary(repo_root, generated_at=_utc_timestamp())

            # Write review_packet.json with severity for this file
            packet_path = repo_root / "dev" / "reports" / "probes" / "latest" / "review_packet.json"
            packet_path.write_text(json.dumps({
                "schema_version": 1,
                "contract_id": "ReviewPacket",
                "hotspots": [
                    {
                        "file": "dev/scripts/example.py",
                        "severity_counts": {"high": 2, "medium": 1},
                    },
                ],
            }), encoding="utf-8")

            # Build graph with repo_root patched
            with patch("dev.scripts.devctl.context_graph.builder.get_repo_root", return_value=repo_root), \
                 patch("dev.scripts.devctl.probe_topology.source_paths.get_repo_root", return_value=repo_root):
                nodes, edges = build_context_graph()

            # Find the source node for our file
            source_node = None
            for node in nodes:
                if node.node_id == "src:dev/scripts/example.py":
                    source_node = node
                    break

            self.assertIsNotNone(source_node, "Expected source node for dev/scripts/example.py")
            self.assertEqual(source_node.metadata.get("severity"), "high")
            self.assertGreater(source_node.temperature, 0.0)

            # Verify the boost is present by comparing against a no-severity baseline
            from dev.scripts.devctl.context_graph.builder import _temperature_for_source, _SEVERITY_BOOST
            base_temp = _temperature_for_source(
                source_node.metadata["fan_in"],
                source_node.metadata["fan_out"],
                source_node.metadata["hint_count"],
                source_node.metadata["changed"],
                severity="",
            )
            self.assertAlmostEqual(
                source_node.temperature - base_temp,
                _SEVERITY_BOOST["high"],
                places=3,
            )
