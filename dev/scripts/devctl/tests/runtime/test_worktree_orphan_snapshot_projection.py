"""Tests for worktree-orphan snapshot projection."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.tests.runtime.test_worktree_orphan_inventory import (
    _init_repo,
    _write,
)
from dev.scripts.devctl.runtime.startup_context import build_startup_context
from dev.scripts.devctl.runtime.worktree_orphan_contracts import (
    OrphanSnapshot,
    build_orphan_inventory_report,
    compute_orphan_snapshot,
    orphan_snapshot_from_mapping,
)


def test_compute_orphan_snapshot_projects_inventory_report(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "codex-voice")
    _write(repo / "bridge.md", "bridge drift\n")

    report = build_orphan_inventory_report(
        repo_root=repo,
        review_state={},
        generated_at_utc="2026-04-22T21:30:00Z",
    )
    snapshot = compute_orphan_snapshot(report, leases=())

    assert isinstance(snapshot, OrphanSnapshot)
    assert snapshot.snapshot_id.startswith("orphan-snapshot-")
    assert snapshot.snapshot_hash.startswith("sha256:")
    assert snapshot.scan_at_utc == report.generated_at_utc
    assert snapshot.derived_from["inventory_report_id"] == report.report_id
    assert snapshot.lease_source == "backfill_pending"
    assert snapshot.ledger_ref == "ledger:not_loaded"
    assert snapshot.stats.total_sources == len(report.sources)
    assert snapshot.sources[0].metadata["snapshot_projection"] == (
        "compute_orphan_snapshot"
    )


def test_compute_orphan_snapshot_hash_is_order_deterministic(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "codex-voice")
    review_state = {
        "review_state": {
            "coordination": {
                "actors": [
                    {
                        "actor_id": "AGENT-2",
                        "presence": "planned",
                        "worktree": "../codex-voice-agent-2",
                        "branch": "feature/agent-2",
                    }
                ]
            }
        }
    }
    report = build_orphan_inventory_report(
        repo_root=repo,
        review_state=review_state,
        generated_at_utc="2026-04-22T21:31:00Z",
    )
    reordered = replace(report, sources=tuple(reversed(report.sources)))

    first = compute_orphan_snapshot(report)
    second = compute_orphan_snapshot(reordered)

    assert first.snapshot_hash == second.snapshot_hash
    assert first.snapshot_id == second.snapshot_id
    assert [source.source_ref for source in first.sources] == [
        source.source_ref for source in second.sources
    ]


def test_orphan_snapshot_round_trips_projection_fields(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "codex-voice")
    report = build_orphan_inventory_report(
        repo_root=repo,
        review_state={},
        generated_at_utc="2026-04-22T21:32:00Z",
    )

    snapshot = compute_orphan_snapshot(report)
    restored = orphan_snapshot_from_mapping(snapshot.to_dict())

    assert restored == snapshot
    assert restored is not None
    assert restored.freshness_requirement == "fresh_scan_required"


def test_startup_context_emits_orphan_snapshot_field() -> None:
    sample = OrphanSnapshot(
        snapshot_id="orphan-snapshot-test",
        scan_at_utc="2026-04-22T21:33:00Z",
        scan_trigger="startup_context",
        scan_scope_applied="bounded_local",
        primary_repo_identity="repo:sha256:test",
        snapshot_hash="sha256:test",
    )

    with patch(
        "dev.scripts.devctl.runtime.startup_context.build_orphan_snapshot_projection",
        return_value=sample,
    ):
        ctx = build_startup_context()

    assert ctx.orphan_snapshot == sample
    assert ctx.to_dict()["orphan_snapshot"]["snapshot_hash"] == "sha256:test"
