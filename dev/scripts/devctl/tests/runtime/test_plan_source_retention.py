"""Tests for durable plan-source retention."""

from __future__ import annotations

from dev.scripts.devctl.runtime.master_plan_contract import PlanRow, SDLCStage
from dev.scripts.devctl.runtime.plan_source_retention import (
    MP377_EXCEPTION_SLICE1_REQUIRED_ANCHORS,
    append_plan_source_snapshot,
    build_plan_source_snapshot,
    full_plan_anchor_status,
    latest_accepted_plan_source_receipt,
    plan_source_body_hash,
    validate_current_plan_source_retention,
    validate_plan_row_source_retention,
)


def test_packet_sourced_plan_row_requires_snapshot() -> None:
    row = PlanRow(
        row_id="MP377-P0-OTHER",
        title="Governed exception receipt contracts",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
        sourced_from_packets=("rev_pkt_3077",),
        content_hash=plan_source_body_hash(
            "Approved Slice 1 plan-source retention addendum."
        ),
    )

    assert validate_plan_row_source_retention(row, ()) == (
        "missing_plan_source_snapshot",
    )


def test_packet_sourced_plan_row_accepts_reconstructable_snapshot() -> None:
    source_text = "Approved Slice 1 plan-source retention addendum."
    row = PlanRow(
        row_id="MP377-P0-OTHER",
        title="Governed exception receipt contracts",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
        sourced_from_packets=("rev_pkt_3077",),
        content_hash=plan_source_body_hash(source_text),
    )
    snapshot = build_plan_source_snapshot(
        plan_row_id=row.row_id,
        source_kind="packet",
        source_ref="packet:rev_pkt_3077",
        source_hash=row.content_hash,
        source_text=source_text,
        captured_at_utc="2026-05-05T23:40:00Z",
        source_packet_id="rev_pkt_3077",
        packet_expires_at_utc="2026-05-06T00:10:00Z",
    )

    assert validate_plan_row_source_retention(row, (snapshot,)) == ()


def test_mp377_exception_slice_requires_full_plan_anchors() -> None:
    source_text = "Approved Slice 1 short summary with matching hash."
    row = PlanRow(
        row_id="MP377-P0-EXC-S1",
        title="Governed exception receipt contracts",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
        sourced_from_packets=("rev_pkt_3077",),
        content_hash=plan_source_body_hash(source_text),
    )
    snapshot = build_plan_source_snapshot(
        plan_row_id=row.row_id,
        source_kind="packet",
        source_ref="packet:rev_pkt_3077",
        source_hash=row.content_hash,
        source_text=source_text,
        captured_at_utc="2026-05-05T23:40:00Z",
        source_packet_id="rev_pkt_3077",
    )

    errors = validate_plan_row_source_retention(row, (snapshot,))

    assert "plan_source_snapshot_not_reconstructable" in errors
    assert "missing_full_plan_anchor:Master architecture" in errors


def test_mp377_exception_slice_accepts_full_plan_anchor_set() -> None:
    source_text = "\n".join(MP377_EXCEPTION_SLICE1_REQUIRED_ANCHORS)
    row = PlanRow(
        row_id="MP377-P0-EXC-S1",
        title="Governed exception receipt contracts",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
        sourced_from_packets=("rev_pkt_3077",),
        content_hash=plan_source_body_hash(source_text),
    )
    snapshot = build_plan_source_snapshot(
        plan_row_id=row.row_id,
        source_kind="packet",
        source_ref="packet:rev_pkt_3077",
        source_hash=row.content_hash,
        source_text=source_text,
        captured_at_utc="2026-05-05T23:40:00Z",
        source_packet_id="rev_pkt_3077",
    )

    assert validate_plan_row_source_retention(row, (snapshot,)) == ()
    status = full_plan_anchor_status(row.row_id, source_text)
    assert status.status == "full_plan_retained"
    assert status.required_count == len(MP377_EXCEPTION_SLICE1_REQUIRED_ANCHORS)
    assert status.matched_count == status.required_count


def test_mp377_current_source_uses_latest_accepted_receipt() -> None:
    full_text = "\n".join(MP377_EXCEPTION_SLICE1_REQUIRED_ANCHORS)
    short_text = "Short summary only"
    full_snapshot = build_plan_source_snapshot(
        plan_row_id="MP377-P0-EXC-S1",
        source_kind="operator_consolidated_plan",
        source_ref="operator:full",
        source_hash=plan_source_body_hash(full_text),
        source_text=full_text,
        captured_at_utc="2026-05-05T23:40:00Z",
    )
    short_snapshot = build_plan_source_snapshot(
        plan_row_id="MP377-P0-EXC-S1",
        source_kind="packet",
        source_ref="packet:short",
        source_hash=plan_source_body_hash(short_text),
        source_text=short_text,
        captured_at_utc="2026-05-06T00:10:00Z",
    )
    row = PlanRow(
        row_id="MP377-P0-EXC-S1",
        title="Governed exception receipt contracts",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
        content_hash=full_snapshot.source_hash,
        work_evidence_ids=(f"plan_source_snapshot:{full_snapshot.snapshot_id}",),
    )
    receipts = (
        _receipt(
            "plan-ingest-old",
            full_snapshot,
            recorded_at_utc="2026-05-05T23:45:00Z",
            completeness="full_plan_retained",
        ),
        _receipt(
            "plan-ingest-new",
            short_snapshot,
            recorded_at_utc="2026-05-06T00:11:00Z",
            completeness="missing_required_anchors",
        ),
    )

    assert validate_plan_row_source_retention(row, (full_snapshot, short_snapshot)) == ()
    latest = latest_accepted_plan_source_receipt(row.row_id, receipts)
    assert latest is not None
    assert latest["receipt_id"] == "plan-ingest-new"
    errors = validate_current_plan_source_retention(
        row,
        (full_snapshot, short_snapshot),
        receipts,
    )

    assert (
        f"plan_row_missing_latest_source_snapshot_ref:{short_snapshot.snapshot_id}"
        in errors
    )
    assert "current_plan_source_snapshot_not_reconstructable" in errors
    assert "current_missing_full_plan_anchor:Master architecture" in errors
    assert "latest_receipt_source_completeness_not_full_plan" in errors


def test_packet_sourced_plan_row_rejects_empty_snapshot_text() -> None:
    row = PlanRow(
        row_id="MP377-P0-EXC-S1",
        title="Governed exception receipt contracts",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
        sourced_from_packets=("rev_pkt_3077",),
    )
    snapshot = build_plan_source_snapshot(
        plan_row_id=row.row_id,
        source_kind="packet",
        source_ref="packet:rev_pkt_3077",
        source_hash="sha256:source",
        source_text="",
        captured_at_utc="2026-05-05T23:40:00Z",
        source_packet_id="rev_pkt_3077",
    )

    errors = validate_plan_row_source_retention(row, (snapshot,))

    assert "plan_source_snapshot_not_reconstructable" in errors


def test_plan_row_with_snapshot_ref_requires_reconstructable_snapshot() -> None:
    row = PlanRow(
        row_id="MP377-P0-EXC-S1",
        title="Governed exception receipt contracts",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
        work_evidence_ids=("plan_source_snapshot:plan-source-missing",),
    )

    assert validate_plan_row_source_retention(row, ()) == (
        "missing_plan_source_snapshot",
    )


def test_plan_source_retention_rejects_hash_mismatch() -> None:
    row = PlanRow(
        row_id="MP377-P0-OTHER",
        title="Governed exception receipt contracts",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
        sourced_from_packets=("rev_pkt_3077",),
        content_hash="sha256:expected",
    )
    snapshot = build_plan_source_snapshot(
        plan_row_id=row.row_id,
        source_kind="packet",
        source_ref="packet:rev_pkt_3077",
        source_hash="sha256:other",
        source_text="Approved Slice 1 plan-source retention addendum.",
        captured_at_utc="2026-05-05T23:40:00Z",
        source_packet_id="rev_pkt_3077",
    )

    assert validate_plan_row_source_retention(row, (snapshot,)) == (
        "plan_source_snapshot_not_reconstructable",
    )


def test_plan_source_snapshot_append_is_idempotent_by_snapshot_id(tmp_path) -> None:
    path = tmp_path / "plan_source_snapshots.jsonl"
    snapshot = build_plan_source_snapshot(
        plan_row_id="MP377-P0-EXC-S1",
        source_kind="chat",
        source_ref="chat:source",
        source_hash="sha256:source",
        source_text="Approved Slice 1 full consolidated plan source.",
        captured_at_utc="2026-05-05T23:40:00Z",
    )

    first = append_plan_source_snapshot(path, snapshot)
    second = append_plan_source_snapshot(path, snapshot)

    assert first.snapshot_id == second.snapshot_id
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def _receipt(
    receipt_id: str,
    snapshot,
    *,
    recorded_at_utc: str,
    completeness: str,
) -> dict[str, object]:
    return {
        "receipt_id": receipt_id,
        "status": "accepted",
        "row_ids": [snapshot.plan_row_id],
        "source_snapshot_ids": [snapshot.snapshot_id],
        "canonical_source_hash": snapshot.body_hash,
        "source_completeness_status": completeness,
        "recorded_at_utc": recorded_at_utc,
    }
