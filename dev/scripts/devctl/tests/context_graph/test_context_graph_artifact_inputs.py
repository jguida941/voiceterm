"""Regression tests for context-graph artifact inputs and topology scanning."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
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


def _utc_timestamp(delta: timedelta | None = None) -> str:
    now = datetime.now(UTC)
    if delta is not None:
        now += delta
    return now.isoformat().replace("+00:00", "Z")


class TestContextGraphArtifactInputs(unittest.TestCase):
    def test_missing_generated_at_falls_back_to_empty_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=None))

            hint_counts, changed_paths, _severity = load_artifact_inputs(repo_root)

        self.assertEqual(hint_counts, {})
        self.assertEqual(changed_paths, set())

    def test_stale_generated_at_falls_back_to_empty_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(
                repo_root,
                _topology_payload(generated_at=_utc_timestamp(delta=timedelta(hours=-7))),
            )

            hint_counts, changed_paths, _severity = load_artifact_inputs(repo_root)

        self.assertEqual(hint_counts, {})
        self.assertEqual(changed_paths, set())

    def test_fresh_generated_at_loads_hint_counts_and_changed_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_topology(repo_root, _topology_payload(generated_at=_utc_timestamp()))

            hint_counts, changed_paths, _severity = load_artifact_inputs(repo_root)

        self.assertEqual(
            hint_counts,
            {"dev/scripts/devctl/context_graph/builder.py": 2},
        )
        self.assertEqual(
            changed_paths,
            {"dev/scripts/devctl/context_graph/builder.py"},
        )


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
