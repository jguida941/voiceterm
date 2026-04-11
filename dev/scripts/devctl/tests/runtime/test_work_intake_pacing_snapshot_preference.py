"""Tests for the saved-snapshot preference on the Step 0 hot path.

Startup-context is the first command every session runs, and repo
policy runs it *before* `context-graph --mode bootstrap`. Before the
Codex P1 fix, `_resolve_graph_inputs` would rebuild the full context
graph whenever the newest saved snapshot's HEAD did not match the
current HEAD, turning every fresh commit into a multi-second Step 0
hang. These tests pin the new contract: we always prefer the saved
snapshot when one exists, even if stale, and only fall through to the
live builder when no snapshot exists at all. The `source` field then
carries a typed freshness marker so downstream consumers can still
see whether the evidence was current, stale, or freshly built.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from dev.scripts.devctl.runtime import work_intake_pacing as pacing_module


def _fake_snapshot(commit_hash: str) -> MagicMock:
    snap = MagicMock()
    snap.commit_hash = commit_hash
    snap.nodes = ()
    snap.edges = ()
    return snap


class ResolveGraphInputsSnapshotPreferenceTests(unittest.TestCase):
    """Typed freshness markers on the saved-snapshot-first path."""

    def _invoke(
        self,
        *,
        snapshot_paths: tuple[str, ...],
        snapshot_commit: str,
        head_commit: str,
        live_nodes: tuple = (),
        live_edges: tuple = (),
    ) -> tuple[tuple, tuple, str, str, MagicMock]:
        with (
            patch.object(
                pacing_module,
                "list_context_graph_snapshots",
                return_value=list(snapshot_paths),
            ) as _list_snaps,
            patch.object(
                pacing_module,
                "load_context_graph_snapshot",
                return_value=_fake_snapshot(snapshot_commit),
            ) as _load_snap,
            patch(
                "dev.scripts.devctl.governance.push_state.current_head_commit_sha",
                return_value=head_commit,
            ) as _head,
            patch(
                "dev.scripts.devctl.context_graph.builder.build_context_graph",
                return_value=(live_nodes, live_edges),
            ) as live_build_mock,
        ):
            result = pacing_module._resolve_graph_inputs(repo_root=Path("/tmp/fake"))
        return (*result, live_build_mock)

    def test_current_snapshot_is_tagged_current_without_live_build(self) -> None:
        """A saved snapshot whose HEAD matches the repo must short-circuit the live builder."""
        _nodes, _edges, source, confidence, live_build_mock = self._invoke(
            snapshot_paths=("/tmp/fake/snap.json",),
            snapshot_commit="abc123",
            head_commit="abc123",
        )

        self.assertEqual(source, "saved_graph_snapshot_current")
        self.assertEqual(confidence, "high")
        live_build_mock.assert_not_called()

    def test_stale_snapshot_is_preferred_over_live_rebuild(self) -> None:
        """The Codex P1 contract: prefer the stale saved snapshot, never rebuild on Step 0."""
        _nodes, _edges, source, confidence, live_build_mock = self._invoke(
            snapshot_paths=("/tmp/fake/snap.json",),
            snapshot_commit="oldsha",
            head_commit="newsha",
        )

        self.assertEqual(source, "saved_graph_snapshot_stale_head")
        # Stale-head freshness is typed as `medium` so consumers can
        # decide how strongly to trust the pacing inputs.
        self.assertEqual(confidence, "medium")
        live_build_mock.assert_not_called()

    def test_missing_head_commit_still_accepts_saved_snapshot(self) -> None:
        """Empty HEAD (detached/fresh init) must still ride the saved snapshot."""
        _nodes, _edges, source, confidence, live_build_mock = self._invoke(
            snapshot_paths=("/tmp/fake/snap.json",),
            snapshot_commit="oldsha",
            head_commit="",
        )

        self.assertEqual(source, "saved_graph_snapshot_current")
        self.assertEqual(confidence, "high")
        live_build_mock.assert_not_called()

    def test_no_snapshot_falls_through_to_live_build(self) -> None:
        """Only when zero snapshots exist should the live builder be touched."""
        _nodes, _edges, source, confidence, live_build_mock = self._invoke(
            snapshot_paths=(),
            snapshot_commit="",
            head_commit="abc123",
            live_nodes=(),
            live_edges=(),
        )

        self.assertEqual(source, "live_context_graph_build")
        self.assertEqual(confidence, "medium")
        live_build_mock.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
