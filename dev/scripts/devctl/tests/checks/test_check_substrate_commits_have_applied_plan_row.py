import json
from pathlib import Path

from dev.scripts.checks.check_substrate_commits_have_applied_plan_row import (
    evaluate_substrate_commits_have_applied_plan_row,
)


def _write_policy(
    tmp_path: Path,
    *,
    observed_at_utc: str = "2026-05-17T06:00:00Z",
) -> Path:
    path = tmp_path / "dev/config/devctl_repo_policy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "repo_governance": {
                    "guard_mandates": {
                        "check_substrate_commits_have_applied_plan_row": {
                            "mandate_packet_id": "rev_pkt_test",
                            "observed_at_utc": observed_at_utc,
                        }
                    },
                    "substrate_commit_plan_rows": {
                        "target_paths": [
                            "dev/scripts/checks/",
                            "dev/scripts/devctl/",
                            "dev/config/",
                            "dev/state/contract_registry.jsonl",
                        ],
                        "ignore_paths": [
                            "dev/scripts/devctl/tests/",
                            "dev/test_data/",
                        ],
                    },
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _write_plan_index(tmp_path: Path, rows: list[dict] | None = None) -> Path:
    path = tmp_path / "dev/state/plan_index.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = rows or []
    payload = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    path.write_text(f"{payload}\n" if payload else "", encoding="utf-8")
    return path


def _write_closure_receipts(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "dev/state/plan_row_closure_receipts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    path.write_text(f"{payload}\n" if payload else "", encoding="utf-8")
    return path


def _closure_receipt(
    commit_sha: str,
    *,
    closure_succeeded: bool | None = True,
    outcome: str = "transitioned_to_applied",
) -> dict:
    payload = {
        "contract_id": "PlanRowClosureReceipt",
        "schema_version": 1,
        "receipt_id": f"plan-row-closure:MP-TEST-GUARD-S1:{commit_sha}:test",
        "plan_row_id": "MP-TEST-GUARD-S1",
        "commit_sha": commit_sha,
        "feature_proof_receipt_path": (
            f"dev/reports/feature_proof_receipts/{commit_sha}.json"
        ),
        "previous_status": "in_progress",
        "next_status": "applied" if closure_succeeded else "",
        "outcome": outcome,
        "commit_anchor_ref": f"commit:{commit_sha}",
        "applied_at_utc": "2026-05-17T06:01:00Z",
        "plan_index_path": "dev/state/plan_index.jsonl",
        "reducer": "commit_to_plan_row_reducer",
    }
    if closure_succeeded is not None:
        payload["closure_succeeded"] = closure_succeeded
    return payload


def _row(
    row_id: str,
    *,
    status: str = "applied",
    commit_anchor_ref: str = "",
    anchor_refs: list[str] | None = None,
) -> dict:
    return {
        "contract_id": "PlanRow",
        "schema_version": 2,
        "row_id": row_id,
        "title": row_id,
        "status": status,
        "sdlc_stage": "impl",
        "commit_anchor_ref": commit_anchor_ref,
        "anchor_refs": anchor_refs or [],
        "work_evidence_ids": [],
        "provenance": {
            "contract_id": "IngestionProvenance",
            "schema_version": 2,
            "observed_at_utc": "2026-05-17T06:01:00Z",
        },
    }


def test_substrate_commit_after_mandate_requires_applied_plan_row(
    tmp_path: Path,
) -> None:
    _write_policy(tmp_path)
    plan_index = _write_plan_index(tmp_path)
    commit_sha = "abcdef1234567890"

    report = evaluate_substrate_commits_have_applied_plan_row(
        repo_root=tmp_path,
        plan_index_path=plan_index,
        commit_shas=(commit_sha,),
        changed_paths_by_commit={
            commit_sha: ("dev/scripts/checks/check_new_guard.py",),
        },
        committed_at_by_commit={commit_sha: "2026-05-17T06:01:00Z"},
    )

    assert report.ok is False
    assert report.substrate_commit_count == 1
    assert report.violation_count == 1
    assert report.violations[0]["reason"] == "missing_applied_plan_row"


def test_applied_plan_row_commit_anchor_covers_substrate_commit(
    tmp_path: Path,
) -> None:
    _write_policy(tmp_path)
    commit_sha = "abcdef1234567890"
    plan_index = _write_plan_index(
        tmp_path,
        [_row("MP-TEST-GUARD-S1", commit_anchor_ref=f"commit:{commit_sha}")],
    )
    _write_closure_receipts(tmp_path, [_closure_receipt(commit_sha)])

    report = evaluate_substrate_commits_have_applied_plan_row(
        repo_root=tmp_path,
        plan_index_path=plan_index,
        commit_shas=(commit_sha,),
        changed_paths_by_commit={
            commit_sha: ("dev/scripts/checks/check_new_guard.py",),
        },
        committed_at_by_commit={commit_sha: "2026-05-17T06:01:00Z"},
    )

    assert report.ok is True
    assert report.covered_commit_count == 1
    assert report.violation_count == 0


def test_post_mandate_applied_plan_row_requires_successful_closure_receipt(
    tmp_path: Path,
) -> None:
    _write_policy(tmp_path)
    commit_sha = "abcdef1234567890"
    plan_index = _write_plan_index(
        tmp_path,
        [_row("MP-TEST-GUARD-S1", commit_anchor_ref=f"commit:{commit_sha}")],
    )

    report = evaluate_substrate_commits_have_applied_plan_row(
        repo_root=tmp_path,
        plan_index_path=plan_index,
        commit_shas=(commit_sha,),
        changed_paths_by_commit={
            commit_sha: ("dev/scripts/checks/check_new_guard.py",),
        },
        committed_at_by_commit={commit_sha: "2026-05-17T06:01:00Z"},
    )

    assert report.ok is False
    assert report.covered_commit_count == 0
    assert report.violation_count == 1
    assert (
        report.violations[0]["reason"]
        == "missing_successful_plan_row_closure_receipt"
    )


def test_legacy_closure_receipt_missing_success_bit_does_not_cover_commit(
    tmp_path: Path,
) -> None:
    _write_policy(tmp_path)
    commit_sha = "abcdef1234567890"
    plan_index = _write_plan_index(
        tmp_path,
        [_row("MP-TEST-GUARD-S1", commit_anchor_ref=f"commit:{commit_sha}")],
    )
    _write_closure_receipts(
        tmp_path,
        [_closure_receipt(commit_sha, closure_succeeded=None)],
    )

    report = evaluate_substrate_commits_have_applied_plan_row(
        repo_root=tmp_path,
        plan_index_path=plan_index,
        commit_shas=(commit_sha,),
        changed_paths_by_commit={
            commit_sha: ("dev/scripts/checks/check_new_guard.py",),
        },
        committed_at_by_commit={commit_sha: "2026-05-17T06:01:00Z"},
    )

    assert report.ok is False
    assert report.violation_count == 1
    assert (
        report.violations[0]["reason"]
        == "missing_successful_plan_row_closure_receipt"
    )


def test_failed_closure_receipt_does_not_cover_commit(tmp_path: Path) -> None:
    _write_policy(tmp_path)
    commit_sha = "abcdef1234567890"
    plan_index = _write_plan_index(
        tmp_path,
        [_row("MP-TEST-GUARD-S1", commit_anchor_ref=f"commit:{commit_sha}")],
    )
    _write_closure_receipts(
        tmp_path,
        [
            _closure_receipt(
                commit_sha,
                closure_succeeded=False,
                outcome="plan_row_missing",
            )
        ],
    )

    report = evaluate_substrate_commits_have_applied_plan_row(
        repo_root=tmp_path,
        plan_index_path=plan_index,
        commit_shas=(commit_sha,),
        changed_paths_by_commit={
            commit_sha: ("dev/scripts/checks/check_new_guard.py",),
        },
        committed_at_by_commit={commit_sha: "2026-05-17T06:01:00Z"},
    )

    assert report.ok is False
    assert report.violation_count == 1
    assert (
        report.violations[0]["reason"]
        == "missing_successful_plan_row_closure_receipt"
    )


def test_short_anchor_ref_covers_full_commit_sha(tmp_path: Path) -> None:
    _write_policy(tmp_path)
    commit_sha = "abcdef1234567890"
    plan_index = _write_plan_index(
        tmp_path,
        [_row("MP-TEST-GUARD-S1", anchor_refs=["commit:abcdef1"])],
    )
    _write_closure_receipts(tmp_path, [_closure_receipt(commit_sha)])

    report = evaluate_substrate_commits_have_applied_plan_row(
        repo_root=tmp_path,
        plan_index_path=plan_index,
        commit_shas=(commit_sha,),
        changed_paths_by_commit={
            commit_sha: ("dev/scripts/devctl/runtime/new_contract.py",),
        },
        committed_at_by_commit={commit_sha: "2026-05-17T06:01:00Z"},
    )

    assert report.ok is True
    assert report.covered_commit_count == 1


def test_non_substrate_commit_is_not_enforced(tmp_path: Path) -> None:
    _write_policy(tmp_path)
    plan_index = _write_plan_index(tmp_path)
    commit_sha = "abcdef1234567890"

    report = evaluate_substrate_commits_have_applied_plan_row(
        repo_root=tmp_path,
        plan_index_path=plan_index,
        commit_shas=(commit_sha,),
        changed_paths_by_commit={commit_sha: ("dev/reports/review_snapshot.md",)},
        committed_at_by_commit={commit_sha: "2026-05-17T06:01:00Z"},
    )

    assert report.ok is True
    assert report.substrate_commit_count == 0


def test_pre_mandate_substrate_gap_is_legacy_not_blocking(tmp_path: Path) -> None:
    _write_policy(tmp_path)
    plan_index = _write_plan_index(tmp_path)
    commit_sha = "abcdef1234567890"

    report = evaluate_substrate_commits_have_applied_plan_row(
        repo_root=tmp_path,
        plan_index_path=plan_index,
        commit_shas=(commit_sha,),
        changed_paths_by_commit={
            commit_sha: ("dev/config/devctl_repo_policy.json",),
        },
        committed_at_by_commit={commit_sha: "2026-05-17T05:59:59Z"},
    )

    assert report.ok is True
    assert report.legacy_gap_count == 1
    assert report.violation_count == 0


def test_offset_timestamp_after_mandate_is_enforced(tmp_path: Path) -> None:
    _write_policy(tmp_path, observed_at_utc="2026-05-17T06:02:38Z")
    plan_index = _write_plan_index(tmp_path)
    commit_sha = "abcdef1234567890"

    report = evaluate_substrate_commits_have_applied_plan_row(
        repo_root=tmp_path,
        plan_index_path=plan_index,
        commit_shas=(commit_sha,),
        changed_paths_by_commit={
            commit_sha: ("dev/scripts/checks/check_new_guard.py",),
        },
        committed_at_by_commit={commit_sha: "2026-05-17T02:09:29-04:00"},
    )

    assert report.ok is False
    assert report.violation_count == 1
    assert report.legacy_gap_count == 0


def test_plan_index_only_backfill_commit_is_not_substrate(tmp_path: Path) -> None:
    _write_policy(tmp_path)
    plan_index = _write_plan_index(tmp_path)
    commit_sha = "abcdef1234567890"

    report = evaluate_substrate_commits_have_applied_plan_row(
        repo_root=tmp_path,
        plan_index_path=plan_index,
        commit_shas=(commit_sha,),
        changed_paths_by_commit={commit_sha: ("dev/state/plan_index.jsonl",)},
        committed_at_by_commit={commit_sha: "2026-05-17T06:01:00Z"},
    )

    assert report.ok is True
    assert report.substrate_commit_count == 0
