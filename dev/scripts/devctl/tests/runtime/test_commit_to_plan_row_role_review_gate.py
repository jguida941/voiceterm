"""R316 Slice 4: T2 RoleReviewReceipt -> commit_to_plan_row closure tests."""

from __future__ import annotations

import pytest

from dev.scripts.devctl.runtime.commit_to_plan_row_role_review_gate import (
    RoleReviewReceiptRequired,
    is_terminal_review_lifecycle,
    lifecycle_covers_plan_row,
    require_terminal_role_review_for_plan_row,
)
from dev.scripts.devctl.runtime.role_review_lifecycle import (
    RoleReviewAssignmentLifecycle,
    RoleReviewReceipt,
)


def _receipt(verdict: str = "approved") -> RoleReviewReceipt:
    return RoleReviewReceipt(
        role="architecture-review",
        packet_id="rev_pkt_4192",
        reviewer_actor="codex",
        verdict=verdict,
        proof_evidence_refs=("pytest::r316_slice4",),
        reviewed_at_utc="2026-05-16T14:58:00Z",
    )


def _reviewed_lifecycle(
    *,
    plan_row_ref: str = "plan_row:MP377-P0-T22AN",
    verdict: str = "approved",
) -> RoleReviewAssignmentLifecycle:
    return RoleReviewAssignmentLifecycle(
        assignment_id="role-review-rev_pkt_4192-architecture",
        packet_id="rev_pkt_4192",
        assigned_role="architecture-review",
        assigned_actor="codex",
        assigned_at_utc="2026-05-16T14:00:00Z",
        due_at_utc="2026-05-16T18:00:00Z",
        status="reviewed",
        receipt=_receipt(verdict=verdict),
        timeout=None,
        parent_bypass_lifecycle_ref=None,
        governed_exception_refs=(),
        evidence_refs=(plan_row_ref,),
    )


def _assigned_lifecycle() -> RoleReviewAssignmentLifecycle:
    return RoleReviewAssignmentLifecycle(
        assignment_id="role-review-rev_pkt_pending",
        packet_id="rev_pkt_pending",
        assigned_role="architecture-review",
        assigned_actor="codex",
        assigned_at_utc="2026-05-16T14:00:00Z",
        due_at_utc="2026-05-16T18:00:00Z",
        status="assigned",
        receipt=None,
        timeout=None,
        parent_bypass_lifecycle_ref=None,
        governed_exception_refs=(),
        evidence_refs=("plan_row:MP377-P0-T22AN",),
    )


def test_closure_succeeds_when_terminal_role_review_exists() -> None:
    lifecycle = _reviewed_lifecycle()

    refs = require_terminal_role_review_for_plan_row(
        "MP377-P0-T22AN",
        role_review_lifecycles=(lifecycle,),
    )

    assert "role_review_assignment:role-review-rev_pkt_4192-architecture" in refs
    assert any(ref.startswith("role_review_receipt:rev_pkt_4192:") for ref in refs)
    assert "role_review_verdict:approved" in refs


def test_closure_raises_when_no_role_review_receipt_for_plan_row() -> None:
    # Lifecycle exists but covers a different plan row.
    other_lifecycle = _reviewed_lifecycle(plan_row_ref="plan_row:OTHER-ROW")

    with pytest.raises(RoleReviewReceiptRequired) as excinfo:
        require_terminal_role_review_for_plan_row(
            "MP377-P0-T22AN",
            role_review_lifecycles=(other_lifecycle,),
        )

    assert excinfo.value.plan_row_id == "MP377-P0-T22AN"
    assert "no role-review lifecycle covers plan_row" in excinfo.value.reason


def test_closure_raises_when_only_non_terminal_receipts_exist() -> None:
    # Assigned-only lifecycle covers the plan row but has no terminal receipt.
    with pytest.raises(RoleReviewReceiptRequired) as excinfo:
        require_terminal_role_review_for_plan_row(
            "MP377-P0-T22AN",
            role_review_lifecycles=(_assigned_lifecycle(),),
        )

    assert "non-terminal" in excinfo.value.reason


def test_closure_includes_role_review_refs_in_composes_with() -> None:
    lifecycle = _reviewed_lifecycle(verdict="changes_requested")

    refs = require_terminal_role_review_for_plan_row(
        "MP377-P0-T22AN",
        role_review_lifecycles=(lifecycle,),
    )

    # composes_with deduplicated typed pointers carry the assignment, receipt,
    # and verdict so PlanRowClosureReceipt can audit the FOURTH-LEG chain.
    assert refs == (
        "role_review_assignment:role-review-rev_pkt_4192-architecture",
        "role_review_receipt:rev_pkt_4192:architecture-review:codex",
        "role_review_verdict:changes_requested",
    )
    assert is_terminal_review_lifecycle(lifecycle) is True
    assert lifecycle_covers_plan_row(lifecycle, "MP377-P0-T22AN") is True
