import json
from pathlib import Path

from dev.scripts.checks import check_receipt_commit_anchor_refs as guard
from dev.scripts.devctl.tests.checks._test_jsonl_helpers import write_jsonl as _write_jsonl


def test_receipt_commit_sha_must_resolve_or_fail(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    _write_jsonl(
        store,
        [
            {
                "contract_id": "ExampleReceipt",
                "receipt_id": "receipt-1",
                "commit_sha": "deadbeef",
            }
        ],
    )

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        commit_exists=lambda sha: False,
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "receipt_commit_sha_unresolved" in reasons


def test_receipt_commit_sha_resolves_passes(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    _write_jsonl(
        store,
        [
            {
                "contract_id": "ExampleReceipt",
                "receipt_id": "receipt-1",
                "commit_sha": "abc123",
            }
        ],
    )

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        commit_exists=lambda sha: sha == "abc123",
    )

    assert report["ok"] is True
    assert report["commit_ref_count"] == 1


def test_external_reference_metadata_allows_nonlocal_sha(tmp_path: Path) -> None:
    receipt = tmp_path / "dev/reports/feature_proof_receipts/external.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(
        json.dumps(
            {
                "contract_id": "FeatureProofReceipt",
                "commit_sha": "7a7afa8520c0d7ca751be3eb889e36b02ea6ebf2",
                "external_reference": {
                    "upstream_repo": "owner/repo",
                    "branch": "main",
                    "reason": "remote branch ancestry proof",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(receipt,),
        commit_exists=lambda sha: False,
    )

    assert report["ok"] is True
    assert report["external_reference_count"] == 1


def test_external_reference_requires_repo_branch_and_reason(tmp_path: Path) -> None:
    receipt = tmp_path / "dev/reports/feature_proof_receipts/external.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(
        json.dumps(
            {
                "contract_id": "FeatureProofReceipt",
                "commit_sha": "7a7afa8520c0d7ca751be3eb889e36b02ea6ebf2",
                "external_reference": {"upstream_repo": "owner/repo"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(receipt,),
        commit_exists=lambda sha: False,
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "receipt_external_reference_incomplete" in reasons
