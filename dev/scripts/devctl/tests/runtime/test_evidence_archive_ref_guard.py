"""Tests for ``evidence_archive_ref_guard`` typed-ref-resolution guard."""

from __future__ import annotations

import pytest

from dev.scripts.devctl.runtime.evidence_archive import (
    EvidenceArchiveReceipt,
    evidence_archive_ref,
)
from dev.scripts.devctl.runtime.evidence_archive_ref_guard import (
    EVIDENCE_ARCHIVE_REF_RESOLUTION_CONTRACT_ID,
    assert_evidence_archive_ref_resolves,
    resolve_evidence_archive_ref,
)


def _receipt(receipt_id: str) -> EvidenceArchiveReceipt:
    return EvidenceArchiveReceipt(
        receipt_id=receipt_id,
        policy_id="evidence-archive-session_activity_log",
        manifest_id="manifest_001",
        lifecycle_ref="lifecycle_001",
        lifecycle_status="closed",
        archive_path="dev/reports/archive/session.tar.zst",
        manifest_path="dev/reports/archive/session.manifest.json",
    )


def test_resolve_with_matching_archive_id_returns_ok() -> None:
    receipts = (_receipt("arc_001"), _receipt("arc_002"))
    ref = evidence_archive_ref("arc_002")

    resolution = resolve_evidence_archive_ref(ref, receipts=receipts)

    assert resolution.ok is True
    assert resolution.found is True
    assert resolution.resolved_archive_id == "arc_002"
    assert resolution.ref == ref
    assert resolution.contract_id == EVIDENCE_ARCHIVE_REF_RESOLUTION_CONTRACT_ID
    assert resolution.schema_version == 1


def test_resolve_with_unknown_ref_returns_not_found() -> None:
    receipts = (_receipt("arc_001"),)
    ref = evidence_archive_ref("arc_does_not_exist")

    resolution = resolve_evidence_archive_ref(ref, receipts=receipts)

    assert resolution.ok is False
    assert resolution.found is False
    assert resolution.resolved_archive_id == ""
    assert "does not resolve" in resolution.diagnostic


def test_resolve_with_empty_ref_returns_not_found() -> None:
    resolution = resolve_evidence_archive_ref("", receipts=(_receipt("arc_001"),))

    assert resolution.ok is False
    assert resolution.found is False
    assert resolution.ref == ""
    assert "empty" in resolution.diagnostic


def test_assert_raises_on_unresolvable_ref() -> None:
    with pytest.raises(ValueError, match="does not resolve"):
        assert_evidence_archive_ref_resolves(
            evidence_archive_ref("missing"),
            receipts=(_receipt("arc_001"),),
        )


def test_assert_returns_resolution_on_match() -> None:
    receipts = (_receipt("arc_777"),)
    resolution = assert_evidence_archive_ref_resolves(
        evidence_archive_ref("arc_777"),
        receipts=receipts,
    )

    assert resolution.ok is True
    assert resolution.resolved_archive_id == "arc_777"
