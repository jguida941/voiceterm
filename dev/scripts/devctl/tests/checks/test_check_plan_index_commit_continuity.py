import json
from pathlib import Path

from dev.scripts.checks.check_plan_index_commit_continuity import (
    evaluate_plan_index_commit_continuity,
)


def _write_plan_index(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "dev/state/plan_index.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    _write_policy(tmp_path)
    return path


def _write_policy(tmp_path: Path) -> Path:
    path = tmp_path / "dev/config/devctl_repo_policy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "repo_governance": {
                    "guard_mandates": {
                        "check_plan_index_commit_continuity": {
                            "mandate_packet_id": "rev_pkt_4017",
                            "observed_at_utc": "2026-05-14T15:37:25Z",
                            "enforced_row_prefixes": ["MP-378-"],
                        }
                    }
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _write_receipts(tmp_path: Path, receipts: list[dict] | None = None) -> Path:
    path = tmp_path / "dev/state/plan_ingestion_receipts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = receipts if receipts is not None else [_receipt("MP-378-LAUNCH-BOOTSTRAP-FIX-S5")]
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    return path


def _receipt(
    row_id: str,
    *,
    receipt_id: str = "plan-ingest-1",
    action_id: str = "plan-intent-action-1",
    status: str = "accepted",
) -> dict:
    return {
        "contract_id": "PlanIntentIngestionReceipt",
        "schema_version": 1,
        "receipt_id": receipt_id,
        "action_id": action_id,
        "status": status,
        "target_kind": "plan_row",
        "row_ids": [row_id],
    }


def _row(
    row_id: str,
    *,
    status: str = "applied",
    mutation_op: str = "implementation_applied",
    anchor_refs: list[str] | None = None,
    work_evidence_ids: list[str] | None = None,
    observed_at_utc: str = "2026-05-14T15:37:25Z",
    sourced_from_packets: list[str] | None = None,
) -> dict:
    return {
        "contract_id": "PlanRow",
        "schema_version": 1,
        "row_id": row_id,
        "title": row_id,
        "status": status,
        "sdlc_stage": "impl",
        "mutation_op": mutation_op,
        "anchor_refs": anchor_refs or [],
        "work_evidence_ids": work_evidence_ids or [],
        "sourced_from_packets": sourced_from_packets or [],
        "provenance": {
            "contract_id": "IngestionProvenance",
            "schema_version": 1,
            "observed_at_utc": observed_at_utc,
        },
    }


def _full_refs() -> tuple[list[str], list[str]]:
    return (
        ["section:MP-378", "commit:abc1234"],
        [
            "plan_intent_receipt:plan-ingest-1",
            "typed_action:plan-intent-action-1",
        ],
    )


def test_mp378_applied_row_requires_full_proof_triple(tmp_path: Path) -> None:
    path = _write_plan_index(
        tmp_path,
        [_row("MP-378-LAUNCH-BOOTSTRAP-FIX-S5")],
    )

    report = evaluate_plan_index_commit_continuity(
        repo_root=tmp_path,
        plan_index_path=path,
    )

    assert report["ok"] is False
    assert report["violation_count"] == 1
    assert report["violations"][0]["missing"] == [
        "commit_anchor_ref",
        "plan_intent_receipt_ref",
        "typed_action_ref",
    ]


def test_mp378_applied_row_accepts_commit_receipt_and_action_refs(
    tmp_path: Path,
) -> None:
    anchor_refs, work_evidence_ids = _full_refs()
    path = _write_plan_index(
        tmp_path,
        [
            _row(
                "MP-378-LAUNCH-BOOTSTRAP-FIX-S5",
                anchor_refs=anchor_refs,
                work_evidence_ids=work_evidence_ids,
            )
        ],
    )
    _write_receipts(tmp_path)

    report = evaluate_plan_index_commit_continuity(
        repo_root=tmp_path,
        plan_index_path=path,
    )

    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_mp378_applied_row_fails_when_receipt_id_is_unknown(tmp_path: Path) -> None:
    anchor_refs, work_evidence_ids = _full_refs()
    path = _write_plan_index(
        tmp_path,
        [
            _row(
                "MP-378-LAUNCH-BOOTSTRAP-FIX-S5",
                anchor_refs=anchor_refs,
                work_evidence_ids=work_evidence_ids,
            )
        ],
    )
    _write_receipts(tmp_path, receipts=[])

    report = evaluate_plan_index_commit_continuity(
        repo_root=tmp_path,
        plan_index_path=path,
    )

    assert report["ok"] is False
    assert "receipt_not_found" in report["violations"][0]["missing"]


def test_mp378_applied_row_fails_when_typed_action_mismatches_receipt(
    tmp_path: Path,
) -> None:
    anchor_refs, work_evidence_ids = _full_refs()
    path = _write_plan_index(
        tmp_path,
        [
            _row(
                "MP-378-LAUNCH-BOOTSTRAP-FIX-S5",
                anchor_refs=anchor_refs,
                work_evidence_ids=work_evidence_ids,
            )
        ],
    )
    _write_receipts(
        tmp_path,
        receipts=[_receipt("MP-378-LAUNCH-BOOTSTRAP-FIX-S5", action_id="other")],
    )

    report = evaluate_plan_index_commit_continuity(
        repo_root=tmp_path,
        plan_index_path=path,
    )

    assert report["ok"] is False
    assert "typed_action_mismatch" in report["violations"][0]["missing"]


def test_legacy_applied_gap_reports_without_blocking_by_default(
    tmp_path: Path,
) -> None:
    path = _write_plan_index(
        tmp_path,
        [
            _row(
                "MP377-LEGACY-S1",
                observed_at_utc="2026-05-01T00:00:00Z",
            )
        ],
    )

    report = evaluate_plan_index_commit_continuity(
        repo_root=tmp_path,
        plan_index_path=path,
    )

    assert report["ok"] is True
    assert report["legacy_gap_count"] == 1
    assert report["violation_count"] == 0


def test_post_mandate_applied_gap_blocks_even_outside_mp378(tmp_path: Path) -> None:
    path = _write_plan_index(
        tmp_path,
        [
            _row(
                "MP379-FUTURE-S1",
                mutation_op="documentation_refresh",
                observed_at_utc="2026-05-14T15:40:00Z",
            )
        ],
    )

    report = evaluate_plan_index_commit_continuity(
        repo_root=tmp_path,
        plan_index_path=path,
    )

    assert report["ok"] is False
    assert report["violations"][0]["row_id"] == "MP379-FUTURE-S1"


def test_strict_legacy_promotes_legacy_gaps_to_violations(tmp_path: Path) -> None:
    path = _write_plan_index(
        tmp_path,
        [
            _row(
                "MP377-LEGACY-S1",
                observed_at_utc="2026-05-01T00:00:00Z",
            )
        ],
    )

    report = evaluate_plan_index_commit_continuity(
        repo_root=tmp_path,
        plan_index_path=path,
        strict_legacy=True,
    )

    assert report["ok"] is False
    assert report["violation_count"] == 1


def test_task_started_packet_binding_row_requires_continuity_when_queued(
    tmp_path: Path,
) -> None:
    path = _write_plan_index(
        tmp_path,
        [
            _row(
                "PKT-BIND-REV-PKT-4013",
                status="queued",
                mutation_op="task_started_packet_binding",
                sourced_from_packets=["rev_pkt_4013"],
                anchor_refs=["packet:rev_pkt_4013", "section:MP-378"],
                work_evidence_ids=[
                    "plan_intent_receipt:plan-ingest-1",
                    "typed_action:plan-intent-action-1",
                ],
            )
        ],
    )
    _write_receipts(tmp_path, receipts=[_receipt("PKT-BIND-REV-PKT-4013")])

    report = evaluate_plan_index_commit_continuity(
        repo_root=tmp_path,
        plan_index_path=path,
    )

    assert report["ok"] is False
    assert report["continuity_row_count"] == 1
    assert report["violation_count"] == 1
    assert report["violations"][0]["row_id"] == "PKT-BIND-REV-PKT-4013"
    assert report["violations"][0]["missing"] == ["commit_anchor_ref"]


def test_guard_discovery_charter_row_requires_continuity_before_applied_status(
    tmp_path: Path,
) -> None:
    anchor_refs, work_evidence_ids = _full_refs()
    path = _write_plan_index(
        tmp_path,
        [
            _row(
                "MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1",
                status="in_progress",
                mutation_op="guard_discovery_build_loop_charter",
                anchor_refs=anchor_refs,
                work_evidence_ids=work_evidence_ids,
            )
        ],
    )
    _write_receipts(
        tmp_path,
        receipts=[_receipt("MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1")],
    )

    report = evaluate_plan_index_commit_continuity(
        repo_root=tmp_path,
        plan_index_path=path,
    )

    assert report["ok"] is True
    assert report["continuity_row_count"] == 1
    assert report["enforced_row_count"] == 1
    assert report["applied_row_count"] == 0
