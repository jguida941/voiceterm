import json
import subprocess
from argparse import Namespace
from pathlib import Path

from dev.scripts.checks import check_current_row_proof_bundle as guard
from dev.scripts.devctl.commands import plan_execution_projection
from dev.scripts.devctl.runtime.current_row_proof_bundle import (
    REQUIRED_GUARD_IDS,
    render_current_row_projection,
)
from dev.scripts.devctl.tests.checks._test_jsonl_helpers import write_jsonl as _write_jsonl


ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"


def _base_paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "plan_index_path": tmp_path / "plan_index.jsonl",
        "snapshots_path": tmp_path / "plan_source_snapshots.jsonl",
        "ingestion_receipts_path": tmp_path / "plan_ingestion_receipts.jsonl",
        "closure_receipts_path": tmp_path / "plan_row_closure_receipts.jsonl",
        "feature_proof_dir": tmp_path / "feature_proof_receipts",
        "guard_output": tmp_path / "guard_runs.jsonl",
        "dogfood_output": tmp_path / "dogfood.jsonl",
        "collaboration": tmp_path / "collaboration.ndjson",
        "final_gate": tmp_path / "final_gate.json",
    }


def _write_source_provenance(paths: dict[str, Path]) -> None:
    _write_jsonl(
        paths["plan_index_path"],
        [
            {
                "contract_id": "PlanRow",
                "row_id": ROW_ID,
                "status": "in_progress",
                "content_hash": "sha256:source",
                "provenance": {"source_hash": "sha256:source"},
                "work_evidence_ids": [
                    "plan_source_snapshot:plan-source-1",
                    "plan_intent_receipt:plan-ingest-1",
                ],
            }
        ],
    )
    _write_jsonl(
        paths["snapshots_path"],
        [
            {
                "contract_id": "PlanSourceSnapshot",
                "snapshot_id": "plan-source-1",
                "plan_row_id": ROW_ID,
                "source_hash": "sha256:source",
                "body_hash": "sha256:source",
                "captured_at_utc": "2026-05-22T12:00:00Z",
            }
        ],
    )
    _write_jsonl(
        paths["ingestion_receipts_path"],
        [
            {
                "contract_id": "PlanIntentIngestionReceipt",
                "receipt_id": "plan-ingest-1",
                "row_ids": [ROW_ID],
                "source_hash": "sha256:source",
                "source_snapshot_ids": ["plan-source-1"],
                "status": "accepted",
                "recorded_at_utc": "2026-05-22T12:01:00Z",
            }
        ],
    )


def _build(paths: dict[str, Path], *, enforce_projection_sync: bool = False) -> dict[str, object]:
    return guard.build_report(
        row_id=ROW_ID,
        plan_index_path=paths["plan_index_path"],
        snapshots_path=paths["snapshots_path"],
        ingestion_receipts_path=paths["ingestion_receipts_path"],
        closure_receipts_path=paths["closure_receipts_path"],
        feature_proof_dir=paths["feature_proof_dir"],
        guard_output_paths=(paths["guard_output"],),
        dogfood_output_paths=(paths["dogfood_output"],),
        collaboration_evidence_paths=(paths["collaboration"],),
        final_gate_paths=(paths["final_gate"],),
        projection_path=paths.get("projection", paths["feature_proof_dir"] / "projection.md"),
        enforce_projection_sync=enforce_projection_sync,
    )


def test_missing_typed_proof_fails_from_typed_state_not_markdown(tmp_path: Path) -> None:
    paths = _base_paths(tmp_path)
    paths["feature_proof_dir"].mkdir()
    paths["closure_receipts_path"].write_text("", encoding="utf-8")
    paths["guard_output"].write_text("", encoding="utf-8")
    paths["dogfood_output"].write_text("", encoding="utf-8")
    paths["collaboration"].write_text("", encoding="utf-8")
    paths["final_gate"].write_text("{}", encoding="utf-8")
    _write_source_provenance(paths)

    report = _build(paths)

    assert report["ok"] is False
    assert report["source_snapshot_id"] == "plan-source-1"
    assert report["ingestion_receipt_id"] == "plan-ingest-1"
    reasons = {failure["reason"] for failure in report["failures"]}
    assert "feature_proof_receipt_missing_typed_proof" in reasons
    assert "dogfood_missing_typed_proof" in reasons


def test_one_way_collaboration_packet_remains_progress_not_green(tmp_path: Path) -> None:
    paths = _base_paths(tmp_path)
    paths["feature_proof_dir"].mkdir()
    paths["closure_receipts_path"].write_text("", encoding="utf-8")
    paths["guard_output"].write_text("", encoding="utf-8")
    paths["dogfood_output"].write_text("", encoding="utf-8")
    paths["final_gate"].write_text("{}", encoding="utf-8")
    _write_source_provenance(paths)
    _write_jsonl(
        paths["collaboration"],
        [
            {
                "event_type": "packet_posted",
                "row_id": ROW_ID,
                "packet_id": "rev_pkt_1",
                "from_agent": "codex",
                "to_agent": "claude",
                "actor_id": "codex",
                "role_id": "reviewer",
                "session_id": "codex-session",
            }
        ],
    )

    report = _build(paths)

    collaboration = report["collaboration_status"]
    assert collaboration["status"] == "progress"
    assert collaboration["codex_to_claude_packet_refs"] == ["rev_pkt_1"]
    assert collaboration["claude_to_codex_packet_refs"] == []
    assert "claude_to_codex" in collaboration["missing_packet_directions"]
    assert "| typed_collaboration | [~] | `progress` |" in render_current_row_projection(report)
    reasons = {failure["reason"] for failure in report["failures"]}
    assert "typed_collaboration_missing_typed_proof" in reasons


def test_loose_chat_collaboration_proof_fails(tmp_path: Path) -> None:
    paths = _base_paths(tmp_path)
    paths["feature_proof_dir"].mkdir()
    paths["closure_receipts_path"].write_text("", encoding="utf-8")
    paths["guard_output"].write_text("", encoding="utf-8")
    paths["dogfood_output"].write_text("", encoding="utf-8")
    paths["final_gate"].write_text("{}", encoding="utf-8")
    _write_source_provenance(paths)
    _write_jsonl(
        paths["collaboration"],
        [
            {
                "source_kind": "loose_chat",
                "row_id": ROW_ID,
                "packet_id": "rev_pkt_1",
                "from_agent": "claude",
                "to_agent": "codex",
                "actor_id": "claude",
                "role_id": "implementer",
                "session_id": "claude-session",
            }
        ],
    )

    report = _build(paths)

    assert report["collaboration_status"]["status"] == "failed"
    reasons = {failure["reason"] for failure in report["failures"]}
    assert "typed_collaboration_failed" in reasons


def test_complete_typed_proof_bundle_passes_and_projection_is_computed(tmp_path: Path) -> None:
    paths = _base_paths(tmp_path)
    paths["feature_proof_dir"].mkdir()
    _write_source_provenance(paths)
    _write_jsonl(
        paths["guard_output"],
        [
            {
                "contract_id": "GuardRunResult",
                "row_id": ROW_ID,
                "guard_id": guard_id,
                "ok": True,
                "receipt_id": f"guard-run-{guard_id}",
            }
            for guard_id in REQUIRED_GUARD_IDS
        ],
    )
    _write_jsonl(
        paths["dogfood_output"],
        [
            {
                "contract_id": "DogfoodRunResult",
                "row_id": ROW_ID,
                "ok": True,
                "run_id": "dogfood-run-1",
            }
        ],
    )
    _write_jsonl(
        paths["collaboration"],
        [
            {
                "contract_id": "ReviewChannelPacketEvidence",
                "row_id": ROW_ID,
                "packet_id": "rev_pkt_1",
                "from_agent": "codex",
                "to_agent": "claude",
                "actor_id": "codex",
                "role_id": "reviewer",
                "session_id": "session-1",
            },
            {
                "contract_id": "ReviewChannelPacketEvidence",
                "row_id": ROW_ID,
                "packet_id": "rev_pkt_2",
                "from_agent": "claude",
                "to_agent": "codex",
                "actor_id": "claude",
                "role_id": "implementer",
                "session_id": "session-2",
            }
        ],
    )
    paths["final_gate"].write_text(
        json.dumps(
            {
                "contract_id": "FinalResponseGateResult",
                "row_id": ROW_ID,
                "final_response_allowed": True,
                "run_id": "final-gate-1",
            }
        ),
        encoding="utf-8",
    )
    (paths["feature_proof_dir"] / "proof.json").write_text(
        json.dumps(
            {
                "contract_id": "FeatureProofReceipt",
                "receipt_id": "fpr-1",
                "feature_id": ROW_ID,
                "real_life_test_status": "proven_passed",
                "tests_run": [
                    "dev/scripts/devctl/tests/checks/"
                    "test_check_current_row_proof_bundle.py::"
                    "test_complete_typed_proof_bundle_passes_and_projection_is_computed"
                ],
                "proven_at_utc": "2026-05-22T12:03:00Z",
            }
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        paths["closure_receipts_path"],
        [
            {
                "contract_id": "PlanRowClosureReceipt",
                "plan_row_id": ROW_ID,
                "receipt_id": "closure-1",
                "closure_succeeded": True,
            }
        ],
    )

    report = _build(paths)
    projection = render_current_row_projection(report)

    assert report["ok"] is True
    assert "| feature_proof_receipt | [x] | `passed` |" in projection
    assert "Generated projection only. This markdown is not durable authority." in projection


def test_projection_sync_rejects_manual_green_without_typed_proof(tmp_path: Path) -> None:
    paths = _base_paths(tmp_path)
    paths["feature_proof_dir"].mkdir()
    paths["closure_receipts_path"].write_text("", encoding="utf-8")
    paths["guard_output"].write_text("", encoding="utf-8")
    paths["dogfood_output"].write_text("", encoding="utf-8")
    paths["collaboration"].write_text("", encoding="utf-8")
    paths["final_gate"].write_text("{}", encoding="utf-8")
    paths["projection"] = tmp_path / "current_row.md"
    paths["projection"].write_text(
        "| ID | Check | Status | Command | Proof ref |\n"
        "|---|---:|---|---|---|\n"
        "| feature_proof_receipt | [x] | `passed` | `manual` | `manual` |\n",
        encoding="utf-8",
    )
    _write_source_provenance(paths)

    report = _build(paths, enforce_projection_sync=True)

    assert report["ok"] is False
    reasons = {failure["reason"] for failure in report["failures"]}
    assert "projection_claims_green_without_typed_proof" in reasons


def test_final_gate_requires_explicit_final_response_permission(tmp_path: Path) -> None:
    paths = _base_paths(tmp_path)
    paths["feature_proof_dir"].mkdir()
    paths["closure_receipts_path"].write_text("", encoding="utf-8")
    paths["guard_output"].write_text("", encoding="utf-8")
    paths["dogfood_output"].write_text("", encoding="utf-8")
    paths["collaboration"].write_text("", encoding="utf-8")
    paths["final_gate"].write_text(
        json.dumps(
            {
                "contract_id": "DevelopNextResult",
                "row_id": ROW_ID,
                "ok": True,
                "status": "continue_required",
                "final_response_gate": {
                    "allow_final_response": False,
                    "next_required_command": "python3 dev/scripts/devctl.py develop launch --dry-run",
                },
            }
        ),
        encoding="utf-8",
    )
    _write_source_provenance(paths)

    report = _build(paths)

    assert report["final_gate_status"]["status"] == "blocked"
    assert report["final_gate_status"]["final_response_allowed"] is False
    reasons = {failure["reason"] for failure in report["failures"]}
    assert "final_gate_blocked" in reasons


def test_current_row_proof_step_records_guard_run_and_regenerates_projection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    paths = _base_paths(tmp_path)
    paths["feature_proof_dir"].mkdir()
    paths["closure_receipts_path"].write_text("", encoding="utf-8")
    paths["guard_output"].write_text("", encoding="utf-8")
    paths["dogfood_output"].write_text("", encoding="utf-8")
    paths["collaboration"].write_text("", encoding="utf-8")
    paths["final_gate"].write_text("{}", encoding="utf-8")
    paths["projection"] = tmp_path / "current_row.md"
    _write_source_provenance(paths)

    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=["python3", "dev/scripts/checks/check_feature_completion.py"],
            returncode=0,
            stdout=json.dumps(
                {
                    "contract_id": "FeatureCompletionGuard",
                    "command": "check_feature_completion",
                    "ok": True,
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(plan_execution_projection.subprocess, "run", fake_run)

    exit_code = plan_execution_projection.run(
        Namespace(
            command="current-row-proof-step",
            row_id=ROW_ID,
            guard_id="check_feature_completion",
            guard_output=paths["guard_output"],
            projection_output=paths["projection"],
            plan_index_path=paths["plan_index_path"],
            snapshots_path=paths["snapshots_path"],
            ingestion_receipts_path=paths["ingestion_receipts_path"],
            closure_receipts_path=paths["closure_receipts_path"],
            feature_proof_dir=paths["feature_proof_dir"],
            dogfood_output=paths["dogfood_output"],
            collaboration_evidence=paths["collaboration"],
            final_gate_output=paths["final_gate"],
            format="json",
        )
    )

    rows = [
        json.loads(line)
        for line in paths["guard_output"].read_text(encoding="utf-8").splitlines()
    ]
    projection = paths["projection"].read_text(encoding="utf-8")

    assert exit_code == 0
    assert rows[0]["contract_id"] == "GuardRunResult"
    assert rows[0]["row_id"] == ROW_ID
    assert rows[0]["guard_id"] == "check_feature_completion"
    assert rows[0]["ok"] is True
    assert "| check_feature_completion | [x] | `passed` |" in projection


def test_current_row_dogfood_records_failed_run_and_regenerates_projection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    paths = _base_paths(tmp_path)
    paths["feature_proof_dir"].mkdir()
    paths["closure_receipts_path"].write_text("", encoding="utf-8")
    paths["guard_output"].write_text("", encoding="utf-8")
    paths["dogfood_output"].write_text("", encoding="utf-8")
    paths["collaboration"].write_text("", encoding="utf-8")
    paths["final_gate"].write_text("{}", encoding="utf-8")
    paths["projection"] = tmp_path / "current_row.md"
    _write_source_provenance(paths)

    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=["python3", "dev/scripts/devctl.py", "check-router", "--execute"],
            returncode=1,
            stdout=json.dumps(
                {
                    "command": "check-router",
                    "row_id": ROW_ID,
                    "ok": False,
                    "failed_commands": ["python3 dev/scripts/checks/check_example.py"],
                }
            ),
            stderr="blocked",
        )

    monkeypatch.setattr(plan_execution_projection.subprocess, "run", fake_run)

    exit_code = plan_execution_projection.run(
        Namespace(
            command="current-row-proof-dogfood",
            row_id=ROW_ID,
            dogfood_output=paths["dogfood_output"],
            projection_output=paths["projection"],
            plan_index_path=paths["plan_index_path"],
            snapshots_path=paths["snapshots_path"],
            ingestion_receipts_path=paths["ingestion_receipts_path"],
            closure_receipts_path=paths["closure_receipts_path"],
            feature_proof_dir=paths["feature_proof_dir"],
            guard_output=paths["guard_output"],
            collaboration_evidence=paths["collaboration"],
            final_gate_output=paths["final_gate"],
            command_timeout_seconds=60,
            route_timeout_seconds=120,
            format="json",
        )
    )

    rows = [
        json.loads(line)
        for line in paths["dogfood_output"].read_text(encoding="utf-8").splitlines()
    ]
    projection = paths["projection"].read_text(encoding="utf-8")

    assert exit_code == 1
    assert rows[0]["contract_id"] == "DogfoodRunResult"
    assert rows[0]["row_id"] == ROW_ID
    assert rows[0]["ok"] is False
    assert "| dogfood | [!] | `failed` |" in projection


def test_current_row_proof_receipt_writes_feature_proof_and_projection(
    tmp_path: Path,
) -> None:
    paths = _base_paths(tmp_path)
    paths["feature_proof_dir"].mkdir()
    paths["closure_receipts_path"].write_text("", encoding="utf-8")
    paths["dogfood_output"].write_text("", encoding="utf-8")
    paths["collaboration"].write_text("", encoding="utf-8")
    paths["final_gate"].write_text("{}", encoding="utf-8")
    paths["projection"] = tmp_path / "current_row.md"
    _write_source_provenance(paths)
    _write_jsonl(
        paths["guard_output"],
        [
            {
                "contract_id": "GuardRunResult",
                "row_id": ROW_ID,
                "guard_id": guard_id,
                "ok": True,
                "receipt_id": f"guard-run-{guard_id}",
                "command": f"python3 dev/scripts/checks/{guard_id}.py --format json",
            }
            for guard_id in REQUIRED_GUARD_IDS
        ],
    )

    exit_code = plan_execution_projection.run(
        Namespace(
            command="current-row-proof-receipt",
            row_id=ROW_ID,
            feature_proof_dir=paths["feature_proof_dir"],
            projection_output=paths["projection"],
            plan_index_path=paths["plan_index_path"],
            snapshots_path=paths["snapshots_path"],
            ingestion_receipts_path=paths["ingestion_receipts_path"],
            closure_receipts_path=paths["closure_receipts_path"],
            guard_output=paths["guard_output"],
            dogfood_output=paths["dogfood_output"],
            collaboration_evidence=paths["collaboration"],
            final_gate_output=paths["final_gate"],
            test_node=[
                "dev/scripts/devctl/tests/checks/test_check_current_row_proof_bundle.py::"
                "test_current_row_proof_receipt_writes_feature_proof_and_projection"
            ],
            evidence_artifact=["command_output:test-python:proof-receipt-test"],
            dogfood_evidence_ref="dogfood:blocked",
            implementer_actor="codex",
            review_fleet_actor="claude",
            review_fleet_role=["current_row_proof_mode"],
            commit_sha="current-row-proof-test",
            format="json",
        )
    )

    receipt_path = paths["feature_proof_dir"] / "current-row-proof-test.json"
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    projection = paths["projection"].read_text(encoding="utf-8")

    assert exit_code == 0
    assert payload["contract_id"] == "FeatureProofReceipt"
    assert payload["feature_id"] == ROW_ID
    assert payload["real_life_test_status"] == "proven_passed"
    assert payload["tests_run"][0].endswith(
        "test_current_row_proof_receipt_writes_feature_proof_and_projection"
    )
    assert "| feature_proof_receipt | [x] | `passed` |" in projection
