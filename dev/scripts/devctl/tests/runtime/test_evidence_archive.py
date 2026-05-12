"""Tests for typed evidence archive contracts."""

from dev.scripts.devctl.runtime.evidence_archive import (
    ARCHIVE_ELIGIBLE_LIFECYCLE_STATUSES,
    EvidenceArchiveEntry,
    EvidenceArchiveManifest,
    EvidenceArchiveReceipt,
    archive_allowed_for_lifecycle_status,
    default_evidence_archive_policy,
    evidence_archive_receipt_from_mapping,
    evidence_archive_ref,
    receipt_preserves_sources,
)


def test_default_evidence_archive_policy_never_deletes_sources() -> None:
    policy = default_evidence_archive_policy("dogfood_receipt")

    assert policy.retention_days == 30
    assert policy.archive_after_lifecycle_statuses == ARCHIVE_ELIGIBLE_LIFECYCLE_STATUSES
    assert policy.delete_source_after_archive is False
    assert policy.manifest_required is True
    assert policy.retrieval_ref_required is True


def test_archive_eligibility_requires_closed_lifecycle() -> None:
    policy = default_evidence_archive_policy("reviewer_audit")

    assert archive_allowed_for_lifecycle_status("closed", policy) is True
    assert archive_allowed_for_lifecycle_status("resolved", policy) is True
    assert archive_allowed_for_lifecycle_status("pending", policy) is False
    assert archive_allowed_for_lifecycle_status("open", policy) is False


def test_archive_manifest_serializes_entries_and_retrieval_refs() -> None:
    entry = EvidenceArchiveEntry(
        source_path="dev/reports/dogfood/runs/receipt.json",
        source_sha256="sha256:abc",
        evidence_kind="dogfood_receipt",
        size_bytes=42,
        lifecycle_ref="plan:MP377",
        lifecycle_status="closed",
        archived_path="dev/reports/archive/receipt.json.zst",
        retrieval_ref="evidence_archive:receipt-1",
    )
    manifest = EvidenceArchiveManifest(
        manifest_id="manifest-1",
        policy_id="evidence-archive-dogfood_receipt",
        archive_path="dev/reports/archive/manifest-1.tar.zst",
        source_root="dev/reports/dogfood/runs",
        head_sha_at_archive="abc123",
        entries=(entry,),
        created_at_utc="2026-05-11T21:20:00Z",
    )

    payload = manifest.to_dict()

    assert payload["contract_id"] == "EvidenceArchiveManifest"
    assert payload["entries"][0]["source_path"] == entry.source_path
    assert payload["entries"][0]["retrieval_ref"] == "evidence_archive:receipt-1"


def test_archive_receipt_round_trips_and_preserves_sources() -> None:
    receipt = EvidenceArchiveReceipt(
        receipt_id="receipt-1",
        policy_id="evidence-archive-dogfood_receipt",
        manifest_id="manifest-1",
        lifecycle_ref="plan:MP377",
        lifecycle_status="closed",
        archive_path="dev/reports/archive/manifest-1.tar.zst",
        manifest_path="dev/reports/archive/manifest-1.json",
        evidence_refs=("packet:rev_pkt_3710",),
        created_at_utc="2026-05-11T21:20:00Z",
    )

    round_tripped = evidence_archive_receipt_from_mapping(receipt.to_dict())

    assert round_tripped == receipt
    assert evidence_archive_ref(receipt.receipt_id) == "evidence_archive:receipt-1"
    assert receipt_preserves_sources(receipt) is True
    assert receipt_preserves_sources(receipt.to_dict()) is True
