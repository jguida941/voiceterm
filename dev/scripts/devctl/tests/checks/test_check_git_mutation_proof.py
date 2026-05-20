from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.checks.check_commit_complete_proof import (
    evaluate_commit_complete_proof,
)
from dev.scripts.checks.check_no_projection_proof_misuse import (
    evaluate_no_projection_proof_misuse,
)
from dev.scripts.checks.check_push_complete_proof import evaluate_push_complete_proof
from dev.scripts.devctl.runtime.correlation_spine import CorrelationContext
from dev.scripts.devctl.runtime.git_mutation_proof_receipt import (
    GitMutationProofReceipt,
    append_git_mutation_proof_receipt,
    build_push_git_mutation_proof_receipt,
    git_mutation_proof_receipt_from_mapping,
)


def test_commit_complete_proof_requires_verified_commit_receipt(tmp_path: Path) -> None:
    report = evaluate_commit_complete_proof(
        repo_root=tmp_path,
        commit_shas=("abc123",),
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "missing_verified_commit_proof"

    append_git_mutation_proof_receipt(
        tmp_path,
        GitMutationProofReceipt(
            receipt_id="git_mutation_proof:commit:abc123",
            mutation_kind="commit",
            expected_sha="abc123",
            observed_local_sha="abc123",
            object_type="commit",
            verified=True,
            status="verified",
        ),
    )

    report = evaluate_commit_complete_proof(
        repo_root=tmp_path,
        commit_shas=("abc123",),
    )

    assert report.ok is True
    assert report.violation_count == 0


def test_git_mutation_proof_receipt_uses_nested_correlation_context() -> None:
    receipt = GitMutationProofReceipt(
        receipt_id="git_mutation_proof:commit:abc123",
        mutation_kind="commit",
        correlation_context=CorrelationContext(
            correlation_id="corr-1",
            causation_id="cause-1",
            run_id="run-1",
        ),
    )

    payload = receipt.to_dict()

    assert payload["correlation_context"]["correlation_id"] == "corr-1"
    assert "correlation_id" not in payload
    assert "causation_id" not in payload
    assert "run_id" not in payload


def test_git_mutation_proof_receipt_reads_legacy_flat_lineage() -> None:
    receipt = git_mutation_proof_receipt_from_mapping(
        {
            "receipt_id": "git_mutation_proof:commit:abc123",
            "mutation_kind": "commit",
            "correlation_id": "corr-legacy",
            "causation_id": "cause-legacy",
            "run_id": "run-legacy",
        }
    )

    assert receipt.correlation_context.correlation_id == "corr-legacy"
    assert receipt.correlation_context.causation_id == "cause-legacy"
    assert receipt.correlation_context.run_id == "run-legacy"


def test_push_complete_proof_requires_remote_ref_match(tmp_path: Path) -> None:
    report = evaluate_push_complete_proof(
        repo_root=tmp_path,
        remote="guardir",
        branch="feature/proof",
        expected_sha="abc123",
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "missing_verified_push_proof"

    append_git_mutation_proof_receipt(
        tmp_path,
        GitMutationProofReceipt(
            receipt_id="git_mutation_proof:push:guardir:feature-proof:abc123",
            mutation_kind="push",
            expected_sha="abc123",
            observed_local_sha="abc123",
            observed_remote_sha="abc123",
            remote_name="guardir",
            branch_name="feature/proof",
            verified=True,
            status="verified",
        ),
    )

    report = evaluate_push_complete_proof(
        repo_root=tmp_path,
        remote="guardir",
        branch="feature/proof",
        expected_sha="abc123",
    )

    assert report.ok is True
    assert report.verified_receipt_count == 1


def test_push_complete_proof_without_claim_is_not_a_live_head_blocker(
    tmp_path: Path,
) -> None:
    report = evaluate_push_complete_proof(
        repo_root=tmp_path,
        remote="guardir",
        branch="feature/proof",
    )

    assert report.ok is True
    assert report.claim_supplied is False
    assert report.violation_count == 0
    assert report.warnings == ("no_expected_push_sha_claim",)


def test_push_mutation_proof_uses_resolved_local_sha_when_supplied(
    tmp_path: Path,
) -> None:
    receipt = build_push_git_mutation_proof_receipt(
        repo_root=tmp_path,
        claim=GitMutationProofReceipt(
            mutation_kind="push",
            remote_name="guardir",
            branch_name="feature/proof",
            expected_sha="abc1234",
            observed_local_sha="abc1234",
            observed_remote_sha="abc1234",
            operation_returned_success=True,
        ),
    )

    assert receipt.verified is True
    assert receipt.observed_local_sha == "abc1234"


def test_projection_proof_misuse_rejects_commit_complete_without_receipt(
    tmp_path: Path,
) -> None:
    progress_path = tmp_path / "dev/reports/progress/events.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(
        json.dumps(
            {
                "phase": "commit.complete",
                "detail": "recorded sha=abc1234; push is next",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = evaluate_no_projection_proof_misuse(
        repo_root=tmp_path,
        progress_path=progress_path,
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == (
        "commit_success_projection_without_git_mutation_proof"
    )

    append_git_mutation_proof_receipt(
        tmp_path,
        GitMutationProofReceipt(
            receipt_id="git_mutation_proof:commit:abc1234",
            mutation_kind="commit",
            expected_sha="abc1234",
            observed_local_sha="abc1234",
            object_type="commit",
            verified=True,
            status="verified",
        ),
    )

    report = evaluate_no_projection_proof_misuse(
        repo_root=tmp_path,
        progress_path=progress_path,
    )

    assert report.ok is True
    assert report.projection_success_claims == 1


def test_projection_proof_misuse_can_ignore_legacy_baseline_lines(
    tmp_path: Path,
) -> None:
    progress_path = tmp_path / "dev/reports/progress/events.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(
        "\n".join(
            (
                json.dumps(
                    {
                        "phase": "commit.complete",
                        "detail": "recorded sha=abc1234; push is next",
                    }
                ),
                json.dumps(
                    {
                        "phase": "commit.complete",
                        "detail": "recorded sha=def5678; push is next",
                    }
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )
    append_git_mutation_proof_receipt(
        tmp_path,
        GitMutationProofReceipt(
            receipt_id="git_mutation_proof:commit:def5678",
            mutation_kind="commit",
            expected_sha="def5678",
            observed_local_sha="def5678",
            object_type="commit",
            verified=True,
            status="verified",
        ),
    )

    report = evaluate_no_projection_proof_misuse(
        repo_root=tmp_path,
        progress_path=progress_path,
        ignore_before_line=1,
    )

    assert report.ok is True
    assert report.ignore_before_line == 1
    assert report.projection_success_claims == 1


def test_projection_proof_misuse_uses_repo_policy_baseline_by_default(
    tmp_path: Path,
) -> None:
    progress_path = tmp_path / "dev/reports/progress/events.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(
        "\n".join(
            (
                json.dumps(
                    {
                        "phase": "commit.complete",
                        "detail": "recorded sha=abc1234; push is next",
                    }
                ),
                json.dumps(
                    {
                        "phase": "commit.complete",
                        "detail": "recorded sha=def5678; push is next",
                    }
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )
    _write_policy_baseline(tmp_path, baseline_line=1)
    append_git_mutation_proof_receipt(
        tmp_path,
        GitMutationProofReceipt(
            receipt_id="git_mutation_proof:commit:def5678",
            mutation_kind="commit",
            expected_sha="def5678",
            observed_local_sha="def5678",
            object_type="commit",
            verified=True,
            status="verified",
        ),
    )

    report = evaluate_no_projection_proof_misuse(
        repo_root=tmp_path,
        progress_path=progress_path,
    )

    assert report.ok is True
    assert report.ignore_before_line == 1
    assert report.ignore_before_line_source == (
        "repo_policy:legacy_progress_baseline_line"
    )
    assert report.projection_success_claims == 1


def _write_policy_baseline(tmp_path: Path, *, baseline_line: int) -> None:
    policy_path = tmp_path / "dev/config/devctl_repo_policy.json"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "repo_governance": {
                    "guard_mandates": {
                        "check_no_projection_proof_misuse": {
                            "mandate_packet_id": "rev_pkt_policy",
                            "observed_at_utc": "2026-05-19T22:13:42Z",
                            "legacy_progress_baseline_line": baseline_line,
                        }
                    }
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
