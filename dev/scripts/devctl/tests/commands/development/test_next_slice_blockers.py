"""Tests for ``next_slice_blockers.artifact_proof_blockers`` consumer."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.commands.development.next_slice_blockers import (
    ARTIFACT_PROOF_MISSING_BLOCKER,
    ARTIFACT_PROOF_STALE_BLOCKER,
    artifact_proof_blockers,
)
from dev.scripts.devctl.runtime.artifact_receipt_ledger import (
    DEFAULT_ARTIFACT_RECEIPT_STORE_REL,
)


def _write_receipt(
    repo_root: Path,
    *,
    slice_id: str,
    ok: bool,
    recorded_at_utc: str,
    receipt_id: str | None = None,
) -> None:
    store = repo_root / DEFAULT_ARTIFACT_RECEIPT_STORE_REL
    store.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "receipt_id": receipt_id or f"art_{slice_id}_{recorded_at_utc}",
        "command": "develop",
        "ok": ok,
        "delivery": "stdout",
        "artifact_format": "json",
        "artifact_path": "",
        "size_bytes": 100,
        "estimated_tokens": 25,
        "artifact_sha256": "a" * 64,
        "summary_keys": [],
        "slice_id": slice_id,
        "actor": "claude",
        "recorded_at_utc": recorded_at_utc,
        "schema_version": 1,
        "contract_id": "ArtifactReceiptRecord",
    }
    with store.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def test_artifact_proof_blockers_missing_when_ledger_empty(tmp_path: Path) -> None:
    blockers = artifact_proof_blockers(
        tmp_path,
        slice_ids=("MP-SLICE-A",),
    )
    assert len(blockers) == 1
    assert blockers[0].slice_id == "MP-SLICE-A"
    assert blockers[0].blocker == ARTIFACT_PROOF_MISSING_BLOCKER
    assert "MP-SLICE-A" in blockers[0].detail


def test_artifact_proof_blockers_stale_when_latest_ok_false(tmp_path: Path) -> None:
    _write_receipt(
        tmp_path,
        slice_id="MP-SLICE-B",
        ok=True,
        recorded_at_utc="2026-05-17T00:00:00+00:00",
    )
    _write_receipt(
        tmp_path,
        slice_id="MP-SLICE-B",
        ok=False,
        recorded_at_utc="2026-05-17T00:30:00+00:00",
        receipt_id="art_stale_001",
    )
    blockers = artifact_proof_blockers(
        tmp_path,
        slice_ids=("MP-SLICE-B",),
        since_seconds=86400 * 365,
    )
    assert len(blockers) == 1
    assert blockers[0].blocker == ARTIFACT_PROOF_STALE_BLOCKER
    assert "art_stale_001" in blockers[0].detail


def test_artifact_proof_blockers_quiet_when_latest_ok_true(tmp_path: Path) -> None:
    _write_receipt(
        tmp_path,
        slice_id="MP-SLICE-C",
        ok=False,
        recorded_at_utc="2026-05-17T00:00:00+00:00",
    )
    _write_receipt(
        tmp_path,
        slice_id="MP-SLICE-C",
        ok=True,
        recorded_at_utc="2026-05-17T00:30:00+00:00",
    )
    blockers = artifact_proof_blockers(
        tmp_path,
        slice_ids=("MP-SLICE-C",),
        since_seconds=86400 * 365,
    )
    assert blockers == ()


def test_artifact_proof_blockers_handles_multiple_slices(tmp_path: Path) -> None:
    _write_receipt(
        tmp_path,
        slice_id="MP-SLICE-OK",
        ok=True,
        recorded_at_utc="2026-05-17T00:30:00+00:00",
    )
    blockers = artifact_proof_blockers(
        tmp_path,
        slice_ids=("MP-SLICE-OK", "MP-SLICE-MISSING"),
        since_seconds=86400 * 365,
    )
    # Only the missing slice surfaces a blocker.
    assert len(blockers) == 1
    assert blockers[0].slice_id == "MP-SLICE-MISSING"
    assert blockers[0].blocker == ARTIFACT_PROOF_MISSING_BLOCKER
