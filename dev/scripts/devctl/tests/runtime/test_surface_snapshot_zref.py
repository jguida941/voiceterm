"""Regression test: snapshot_id must be invariant when only zref changes."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime.surface_snapshot import build_surface_snapshot_id


class TestSnapshotIdZrefInvariance(unittest.TestCase):

    def test_snapshot_id_invariant_when_zref_differs(self) -> None:
        pipeline_without_zref = {
            "pipeline_id": "test-pipe",
            "state": "approved",
            "approval_state": "approved",
        }
        pipeline_with_zref = {
            **pipeline_without_zref,
            "zref": "zref_abc12345_def67890",
        }
        id_without = build_surface_snapshot_id(commit_pipeline=pipeline_without_zref)
        id_with = build_surface_snapshot_id(commit_pipeline=pipeline_with_zref)
        self.assertEqual(
            id_without,
            id_with,
            "snapshot_id must not change when only zref differs — zref is derived from snapshot_id and must be excluded from the hash",
        )

    def test_snapshot_id_invariant_when_snapshot_id_present(self) -> None:
        pipeline_without = {"pipeline_id": "test-pipe", "state": "approved"}
        pipeline_with = {
            **pipeline_without,
            "snapshot_id": "snap-abc12345",
            "zref": "zref_abc12345_def67890",
        }
        id_without = build_surface_snapshot_id(commit_pipeline=pipeline_without)
        id_with = build_surface_snapshot_id(commit_pipeline=pipeline_with)
        self.assertEqual(id_without, id_with)


if __name__ == "__main__":
    unittest.main()
