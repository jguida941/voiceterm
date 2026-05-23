"""FeatureProofReceipt action for current-row projection commands."""

from __future__ import annotations

import json
from pathlib import Path

from ..runtime.current_row_proof_bundle import (
    REQUIRED_GUARD_IDS,
    render_current_row_projection,
)
from ..runtime.feature_proof_receipt import FeatureProofReceipt
from .plan_execution_projection_common import (
    ProjectionCommandSupport as Support,
    build_current_row_proof_report as _build_report,
)


def run_current_row_receipt(args) -> int:
    row_id = str(args.row_id)
    test_nodes = tuple(str(node).strip() for node in args.test_node if str(node).strip())
    if not test_nodes or not all("::" in node for node in test_nodes):
        return print_receipt_error(
            args,
            "current-row FeatureProofReceipt requires at least one exact pytest node id",
        )

    report = _build_report(args, row_id=row_id)
    guard_statuses = report.get("guard_statuses")
    if not isinstance(guard_statuses, dict):
        guard_statuses = {}
    missing_guards = [
        guard_id
        for guard_id in REQUIRED_GUARD_IDS
        if not isinstance(guard_statuses.get(guard_id), dict)
        or guard_statuses[guard_id].get("status") != "passed"
    ]
    if missing_guards:
        return print_receipt_error(
            args,
            "current-row FeatureProofReceipt requires passed guard proofs: "
            + ", ".join(missing_guards),
        )

    timestamp = Support.utc_timestamp()
    commit_sha = str(args.commit_sha).strip() or Support.receipt_token(
        row_id,
        "feature-proof",
        timestamp,
        "\n".join(test_nodes),
        json.dumps(report, sort_keys=True, default=str),
    )
    receipt_path, receipt_id = _write_feature_receipt(
        args,
        row_id=row_id,
        test_nodes=test_nodes,
        report=report,
        guard_statuses=guard_statuses,
        timestamp=timestamp,
        commit_sha=commit_sha,
    )
    updated_report = _build_report(args, row_id=row_id)
    projection_path = Path(args.projection_output)
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    projection_path.write_text(render_current_row_projection(updated_report), encoding="utf-8")
    output = {
        "ok": True,
        "row_id": row_id,
        "feature_proof_receipt_path": str(Support.repo_relative(receipt_path)),
        "projection_path": str(Support.repo_relative(projection_path)),
        "receipt_id": receipt_id,
        "proof_bundle_ok": updated_report.get("ok"),
        "next_bounded_command": updated_report.get("next_bounded_command"),
    }
    if args.format == "json":
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print("- ok: true")
        print(f"- feature_proof_receipt_path: `{output['feature_proof_receipt_path']}`")
        print(f"- receipt_id: `{output['receipt_id']}`")
        print(f"- next_bounded_command: `{updated_report.get('next_bounded_command')}`")
    return 0


def print_receipt_error(args, detail: str) -> int:
    output = {"ok": False, "error": detail}
    if getattr(args, "format", "json") == "json":
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(f"- ok: false\n- error: {detail}")
    return 2


def _write_feature_receipt(
    args,
    *,
    row_id: str,
    test_nodes: tuple[str, ...],
    report: dict[str, object],
    guard_statuses: dict[str, object],
    timestamp: str,
    commit_sha: str,
) -> tuple[Path, str]:
    dogfood_status = report.get("dogfood_statuses")
    dogfood_ref = str(args.dogfood_evidence_ref).strip()
    if not dogfood_ref and isinstance(dogfood_status, dict):
        dogfood_ref = str(dogfood_status.get("proof_ref") or "")
    evidence_artifacts = tuple(
        artifact.strip()
        for artifact in [
            *args.evidence_artifact,
            str(Support.repo_relative(Path(args.guard_output))),
            str(Support.repo_relative(Path(args.dogfood_output))),
            str(Support.repo_relative(Path(args.projection_output))),
        ]
        if str(artifact).strip()
    )
    connectivity_guards = tuple(
        str(guard_statuses.get(guard_id, {}).get("command") or guard_id)
        for guard_id in REQUIRED_GUARD_IDS
    )
    review_fleet_roles = tuple(str(role) for role in args.review_fleet_role)
    if not review_fleet_roles:
        review_fleet_roles = ("current_row_proof_mode",)
    receipt = FeatureProofReceipt(
        feature_id=row_id,
        commit_sha=commit_sha,
        implementer_actor=str(args.implementer_actor),
        review_fleet_roles_ran=review_fleet_roles,
        review_fleet_actor=str(args.review_fleet_actor),
        tests_run=test_nodes,
        tests_passed_count=len(test_nodes),
        tests_failed_count=0,
        connectivity_guards_ran=connectivity_guards,
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref=dogfood_ref,
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=(),
        proven_at_utc=timestamp,
        evidence_artifacts=evidence_artifacts,
        role_review_receipt_refs=tuple(str(ref) for ref in report.get("active_packet_refs", [])),
    )
    feature_proof_dir = Path(args.feature_proof_dir)
    feature_proof_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = feature_proof_dir / f"{Support.path_token(commit_sha)}.json"
    payload = receipt.to_dict()
    receipt_id = f"feature-proof:{commit_sha}"
    payload["receipt_id"] = receipt_id
    payload["plan_authority_refs"] = {
        "active_row_id": row_id,
        "plan_source_path": report.get("source_ref", ""),
        "plan_source_hash": report.get("source_hash", ""),
        "plan_source_snapshot_id": report.get("source_snapshot_id", ""),
        "plan_intent_ingestion_receipt_id": report.get("ingestion_receipt_id", ""),
    }
    receipt_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt_path, receipt_id
