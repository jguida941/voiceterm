from __future__ import annotations

import pytest

from dev.scripts.devctl.runtime.role_review_lifecycle import (
    ROLE_REVIEW_ASSIGNMENT_LIFECYCLE_CONTRACT_ID,
    ROLE_REVIEW_RECEIPT_CONTRACT_ID,
    ROLE_REVIEW_SCHEMA_VERSION,
    ROLE_REVIEW_TIMEOUT_CONTRACT_ID,
    RoleReviewAssignmentLifecycle,
    RoleReviewReceipt,
    RoleReviewTimeout,
    role_review_assignment_lifecycle_from_mapping,
    role_review_receipt_from_mapping,
)


def test_role_review_receipt_serializes_terminal_review_proof() -> None:
    receipt = _receipt(verdict="changes_requested")

    payload = receipt.to_dict()

    assert payload["contract_id"] == ROLE_REVIEW_RECEIPT_CONTRACT_ID
    assert payload["schema_version"] == ROLE_REVIEW_SCHEMA_VERSION
    assert payload["role"] == "architecture-review"
    assert payload["packet_id"] == "rev_pkt_4192"
    assert payload["reviewer_actor"] == "codex"
    assert payload["verdict"] == "changes_requested"
    assert payload["proof_evidence_refs"] == [
        "pytest::test_role_review_receipt_serializes_terminal_review_proof"
    ]
    assert payload["reviewed_at_utc"] == "2026-05-16T14:58:00Z"


def test_reviewed_lifecycle_requires_matching_receipt() -> None:
    lifecycle = _reviewed_lifecycle()

    payload = lifecycle.to_dict()

    assert payload["contract_id"] == ROLE_REVIEW_ASSIGNMENT_LIFECYCLE_CONTRACT_ID
    assert payload["schema_version"] == ROLE_REVIEW_SCHEMA_VERSION
    assert payload["assignment_id"] == "role-review-rev_pkt_4192-architecture"
    assert payload["status"] == "reviewed"
    assert payload["receipt"]["contract_id"] == ROLE_REVIEW_RECEIPT_CONTRACT_ID
    assert payload["receipt"]["verdict"] == "approved"
    assert payload["timeout"] is None
    assert payload["parent_bypass_lifecycle_ref"] == (
        "gel:bypass:bypass:grant-20260516T054109743503"
    )
    assert payload["governed_exception_refs"] == ["gel:exception:role-review"]
    assert payload["evidence_refs"] == ["packet:rev_pkt_4192"]

    with pytest.raises(ValueError, match="receipt role"):
        RoleReviewAssignmentLifecycle(
            **{
                **_reviewed_lifecycle_kwargs(),
                "receipt": _receipt(role="dogfood-test"),
            }
        )

    with pytest.raises(ValueError, match="receipt packet"):
        RoleReviewAssignmentLifecycle(
            **{
                **_reviewed_lifecycle_kwargs(),
                "receipt": _receipt(packet_id="rev_pkt_other"),
            }
        )


def test_timed_out_lifecycle_requires_matching_timeout() -> None:
    timeout = RoleReviewTimeout(
        role="architecture-review",
        packet_id="rev_pkt_4192",
        timed_out_at_utc="2026-05-16T16:58:00Z",
        fallback_authority="operator:R260",
    )
    lifecycle = RoleReviewAssignmentLifecycle(
        assignment_id="role-review-rev_pkt_4192-timeout",
        packet_id="rev_pkt_4192",
        assigned_role="architecture-review",
        assigned_actor="codex",
        assigned_at_utc="2026-05-16T14:47:58Z",
        due_at_utc="2026-05-16T16:47:58Z",
        status="timed_out",
        receipt=None,
        timeout=timeout,
        parent_bypass_lifecycle_ref=None,
        governed_exception_refs=(),
        evidence_refs=("packet:rev_pkt_4192",),
    )

    payload = lifecycle.to_dict()

    assert payload["status"] == "timed_out"
    assert payload["receipt"] is None
    assert payload["timeout"]["contract_id"] == ROLE_REVIEW_TIMEOUT_CONTRACT_ID
    assert payload["timeout"]["fallback_authority"] == "operator:R260"
    assert payload["timeout"]["timed_out_at_utc"] == "2026-05-16T16:58:00Z"

    with pytest.raises(ValueError, match="timed_out assignments require"):
        RoleReviewAssignmentLifecycle(
            **{
                **_reviewed_lifecycle_kwargs(),
                "status": "timed_out",
                "receipt": None,
                "timeout": None,
            }
        )


def test_assigned_lifecycle_rejects_terminal_evidence() -> None:
    lifecycle = RoleReviewAssignmentLifecycle(
        assignment_id="role-review-rev_pkt_4192-open",
        packet_id="rev_pkt_4192",
        assigned_role="architecture-review",
        assigned_actor="codex",
        assigned_at_utc="2026-05-16T14:47:58Z",
        due_at_utc="2026-05-16T16:47:58Z",
        status="assigned",
        receipt=None,
        timeout=None,
        parent_bypass_lifecycle_ref=None,
        governed_exception_refs=(),
        evidence_refs=("packet:rev_pkt_4192",),
    )

    assert lifecycle.to_dict()["status"] == "assigned"

    with pytest.raises(ValueError, match="assigned lifecycle state"):
        RoleReviewAssignmentLifecycle(
            **{
                **_reviewed_lifecycle_kwargs(),
                "status": "assigned",
            }
        )


def test_mapping_helpers_reject_invalid_status_and_verdict() -> None:
    with pytest.raises(ValueError, match="invalid role review verdict"):
        role_review_receipt_from_mapping(
            {
                "role": "architecture-review",
                "packet_id": "rev_pkt_4192",
                "reviewer_actor": "codex",
                "verdict": "rubber_stamped",
                "proof_evidence_refs": ["pytest::invalid"],
                "reviewed_at_utc": "2026-05-16T14:58:00Z",
            }
        )

    with pytest.raises(ValueError, match="invalid role review assignment status"):
        role_review_assignment_lifecycle_from_mapping(
            {
                **_reviewed_lifecycle().to_dict(),
                "status": "unreviewed",
            }
        )


def _receipt(
    *,
    role: str = "architecture-review",
    packet_id: str = "rev_pkt_4192",
    verdict: str = "approved",
) -> RoleReviewReceipt:
    return RoleReviewReceipt(
        role=role,
        packet_id=packet_id,
        reviewer_actor="codex",
        verdict=verdict,
        proof_evidence_refs=(
            "pytest::test_role_review_receipt_serializes_terminal_review_proof",
        ),
        reviewed_at_utc="2026-05-16T14:58:00Z",
    )


def _reviewed_lifecycle_kwargs() -> dict[str, object]:
    return {
        "assignment_id": "role-review-rev_pkt_4192-architecture",
        "packet_id": "rev_pkt_4192",
        "assigned_role": "architecture-review",
        "assigned_actor": "codex",
        "assigned_at_utc": "2026-05-16T14:47:58Z",
        "due_at_utc": "2026-05-16T16:47:58Z",
        "status": "reviewed",
        "receipt": _receipt(),
        "timeout": None,
        "parent_bypass_lifecycle_ref": (
            "gel:bypass:bypass:grant-20260516T054109743503"
        ),
        "governed_exception_refs": ("gel:exception:role-review",),
        "evidence_refs": ("packet:rev_pkt_4192",),
    }


def _reviewed_lifecycle() -> RoleReviewAssignmentLifecycle:
    return RoleReviewAssignmentLifecycle(**_reviewed_lifecycle_kwargs())
