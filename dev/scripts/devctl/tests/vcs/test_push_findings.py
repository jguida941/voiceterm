"""Regression coverage for governed-push finding contract routing."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.vcs.push_findings import (
    BRANCH_IDENTITY_VIOLATION,
    build_push_finding,
)
from dev.scripts.devctl.governance_review.models import GovernanceReviewInput
from dev.scripts.devctl.runtime.platform_finding_ingest import (
    PLATFORM_FINDING_INGEST_CONTRACT_ID,
    PlatformFindingIngest,
)


def test_push_finding_uses_canonical_finding_and_ingest_payload(tmp_path: Path) -> None:
    state = SimpleNamespace(repo_root=str(tmp_path))

    finding = build_push_finding(
        state,
        BRANCH_IDENTITY_VIOLATION,
        "Configured branch does not match live git branch.",
        evidence={"configured_branch": "feature/demo"},
    )

    assert finding["contract_id"] == "Finding"
    assert finding["signal_type"] == "guard"
    assert finding["check_id"] == "vcs.push.execution_truth"
    assert finding["rule_id"] == "vcs.push.branch_identity"
    assert finding["type"] == "BranchIdentityViolation"
    assert finding["message"] == "Configured branch does not match live git branch."
    assert finding["evidence"]["configured_branch"] == "feature/demo"
    assert finding["platform_finding_ingest"]["contract_id"] == (
        PLATFORM_FINDING_INGEST_CONTRACT_ID
    )
    review_input = finding["platform_finding_ingest"]["review_input"]
    assert review_input["finding_id"] == finding["finding_id"]
    assert review_input["finding_class"] == "authority_boundary"
    assert review_input["prevention_surface"] == "authority_rule"
    assert review_input["recurrence_risk"] == "systemic"


def test_push_finding_payload_records_through_platform_ingest(tmp_path: Path) -> None:
    governance_log = tmp_path / "finding_reviews.jsonl"
    summary_root = tmp_path / "summary"
    promotion_queue = tmp_path / "promotion.jsonl"
    state = SimpleNamespace(repo_root=str(tmp_path))
    finding = build_push_finding(
        state,
        BRANCH_IDENTITY_VIOLATION,
        "Configured branch does not match live git branch.",
    )

    result = PlatformFindingIngest(
        repo_root=tmp_path,
        governance_log_path=governance_log,
        governance_summary_root=summary_root,
        promotion_queue_path=promotion_queue,
    ).record_review_input(
        GovernanceReviewInput(
            **finding["platform_finding_ingest"]["review_input"],
        )
    )

    assert result.status == "recorded"
    assert result.row is not None
    assert result.row["finding_id"] == finding["finding_id"]
    assert result.row["signal_type"] == "guard"
    assert result.finding is not None
    assert result.finding["contract_id"] == "Finding"
    assert (summary_root / "review_summary.json").is_file()
