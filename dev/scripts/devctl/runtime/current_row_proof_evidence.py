"""Typed evidence readers for current-row proof mode."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from .current_row_proof_config import REQUIRED_GUARD_IDS
from .current_row_proof_utils import ProofUtils as U


class ProofEvidence:
    """Read source, guard, dogfood, gate, receipt, and closure proof evidence."""

    @staticmethod
    def find_plan_row(rows: Sequence[Mapping[str, object]], row_id: str) -> dict[str, object]:
        for row in rows:
            if row.get("contract_id") == "PlanRow" and row.get("row_id") == row_id:
                return dict(row)
        return {}

    @staticmethod
    def find_source_snapshot(*, snapshots_path: Path, row_id: str, snapshot_id: str) -> dict[str, object]:
        latest: dict[str, object] = {}
        for snapshot in U.iter_jsonish(snapshots_path):
            if snapshot.get("contract_id") != "PlanSourceSnapshot":
                continue
            if snapshot_id and snapshot.get("snapshot_id") == snapshot_id:
                return dict(snapshot)
            if str(snapshot.get("plan_row_id") or "") == row_id:
                latest = dict(snapshot)
        return latest

    @staticmethod
    def find_ingestion_receipt(
        *,
        ingestion_receipts_path: Path,
        row_id: str,
        receipt_id: str,
        snapshot_id: str,
    ) -> dict[str, object]:
        latest: dict[str, object] = {}
        for receipt in U.iter_jsonish(ingestion_receipts_path):
            if receipt.get("contract_id") != "PlanIntentIngestionReceipt":
                continue
            if receipt_id and receipt.get("receipt_id") == receipt_id:
                return dict(receipt)
            row_ids = set(U.strings(receipt.get("row_ids")))
            snapshot_ids = set(U.strings(receipt.get("source_snapshot_ids")))
            if row_id in row_ids or (snapshot_id and snapshot_id in snapshot_ids):
                latest = dict(receipt)
        return latest

    @staticmethod
    def guard_statuses(paths: Sequence[Path], *, row_id: str) -> dict[str, dict[str, object]]:
        statuses = {
            guard_id: {"status": "missing", "proof_ref": "", "command": U.guard_command(guard_id)}
            for guard_id in REQUIRED_GUARD_IDS
        }
        for payload in U.iter_jsonish_many(paths):
            for row in ProofEvidence.flatten_guard_payload(payload):
                guard_id = ProofEvidence.guard_id(row)
                if guard_id not in statuses or not U.payload_refs_row(row, row_id):
                    continue
                ok = U.truthy(row.get("ok")) or str(row.get("status") or "").lower() in {
                    "passed",
                    "ok",
                    "green",
                }
                statuses[guard_id] = {
                    "status": "passed" if ok else "failed",
                    "proof_ref": str(
                        row.get("receipt_id")
                        or row.get("proof_ref")
                        or row.get("run_id")
                        or row.get("path")
                        or guard_id
                    ),
                    "command": str(row.get("command") or U.guard_command(guard_id)),
                    "timestamp": str(row.get("timestamp") or row.get("timestamp_utc") or ""),
                }
        return statuses

    @staticmethod
    def flatten_guard_payload(payload: Mapping[str, object]) -> Iterable[Mapping[str, object]]:
        yield payload
        for key in ("guards", "guard_outputs", "steps", "planned_commands"):
            for item in U.sequence_of_mappings(payload.get(key)):
                yield item
        steps = payload.get("steps")
        if isinstance(steps, Sequence) and not isinstance(steps, (str, bytes)):
            for step in steps:
                if isinstance(step, Mapping):
                    yield from ProofEvidence.flatten_guard_payload(step)

    @staticmethod
    def guard_id(payload: Mapping[str, object]) -> str:
        for key in ("guard_id", "script_id", "command", "id", "name"):
            value = str(payload.get(key) or "")
            for guard_id in REQUIRED_GUARD_IDS:
                if guard_id in value or guard_id.removeprefix("check_") in value:
                    return guard_id
        return ""

    @staticmethod
    def dogfood_statuses(paths: Sequence[Path], *, row_id: str) -> dict[str, object]:
        latest: dict[str, object] = {}
        for payload in U.iter_jsonish_many(paths):
            if U.payload_refs_row(payload, row_id):
                latest = dict(payload)
        if not latest:
            return {"status": "missing", "proof_ref": ""}
        status = str(latest.get("status") or latest.get("dogfood_status") or "").lower()
        ok = U.truthy(latest.get("ok")) or status in {"passed", "ok", "green"}
        return {
            "status": "passed" if ok else "failed",
            "proof_ref": str(
                latest.get("receipt_id")
                or latest.get("run_id")
                or latest.get("dogfood_record_id")
                or latest.get("path")
                or "dogfood"
            ),
            "timestamp": str(latest.get("timestamp") or latest.get("timestamp_utc") or ""),
        }

    @staticmethod
    def final_gate_status(paths: Sequence[Path], *, row_id: str) -> dict[str, object]:
        latest: dict[str, object] = {}
        for payload in U.iter_jsonish_many(paths):
            if U.payload_refs_row(payload, row_id):
                latest = dict(payload)
        if not latest:
            return {"status": "missing", "proof_ref": "", "final_response_allowed": False}
        allowed = ProofEvidence.explicit_final_response_allowed(latest)
        return {
            "status": "passed" if allowed else "blocked",
            "proof_ref": str(latest.get("receipt_id") or latest.get("run_id") or "final_gate"),
            "final_response_allowed": allowed,
            "timestamp": str(latest.get("timestamp") or latest.get("timestamp_utc") or ""),
        }

    @staticmethod
    def explicit_final_response_allowed(payload: Mapping[str, object]) -> bool:
        for key in ("final_response_allowed", "final_response_gate_allowed"):
            if key in payload:
                return U.truthy(payload.get(key))
        for nested_key in ("final_response_gate", "final_response_stop", "final_gate"):
            nested = payload.get(nested_key)
            if not isinstance(nested, Mapping):
                continue
            for key in ("final_response_allowed", "final_response_gate_allowed", "allow_final_response"):
                if key in nested:
                    return U.truthy(nested.get(key))
        return False

    @staticmethod
    def feature_proof_status(root: Path, *, row_id: str) -> dict[str, object]:
        best: dict[str, object] = {"status": "missing", "receipt_id": "", "tests_run": []}
        if not root.exists():
            return best
        for path in sorted(root.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(payload, Mapping) or payload.get("contract_id") != "FeatureProofReceipt":
                continue
            if not ProofEvidence.feature_proof_refs_row(payload, row_id):
                continue
            tests_run = tuple(U.strings(payload.get("tests_run")))
            proven = payload.get("real_life_test_status") == "proven_passed"
            has_pytest_node = any("::" in test_ref for test_ref in tests_run)
            has_required_node = any("test_check_current_row_proof_bundle.py::" in test_ref for test_ref in tests_run)
            receipt = {
                "status": "passed" if proven and has_pytest_node and has_required_node else "failed",
                "receipt_id": str(payload.get("receipt_id") or path.name),
                "path": str(U.repo_relative(path)),
                "tests_run": list(tests_run),
                "real_life_test_status": str(payload.get("real_life_test_status") or ""),
                "required_pytest_node_present": has_required_node,
                "proven_at_utc": str(payload.get("proven_at_utc") or ""),
            }
            if receipt["status"] == "passed":
                return receipt
            best = receipt
        return best

    @staticmethod
    def feature_proof_refs_row(payload: Mapping[str, object], row_id: str) -> bool:
        direct_refs = (
            payload.get("plan_row_id"),
            payload.get("row_id"),
            payload.get("feature_id"),
            payload.get("target_ref"),
        )
        if any(str(ref) == row_id or str(ref).endswith(f":{row_id}") for ref in direct_refs):
            return True
        for field in (
            "plan_row_ids",
            "plan_refs",
            "evidence_artifacts",
            "role_review_receipt_refs",
            "bypass_audit_trail_refs",
            "tests_run",
            "connectivity_guards_ran",
        ):
            if any(row_id in str(item) for item in U.strings(payload.get(field))):
                return True
        return False

    @staticmethod
    def closure_status(path: Path, *, row_id: str) -> dict[str, object]:
        for receipt in U.iter_jsonish(path):
            if receipt.get("contract_id") != "PlanRowClosureReceipt":
                continue
            if str(receipt.get("plan_row_id") or receipt.get("row_id") or "") != row_id:
                continue
            if U.truthy(receipt.get("closure_succeeded")):
                return {
                    "status": "passed",
                    "receipt_id": str(receipt.get("receipt_id") or receipt.get("closure_receipt_id") or ""),
                }
        return {"status": "missing", "receipt_id": ""}

    @staticmethod
    def test_statuses(feature_proof: Mapping[str, object]) -> dict[str, object]:
        tests_run = tuple(U.strings(feature_proof.get("tests_run")))
        return {
            "status": "passed" if feature_proof.get("status") == "passed" else "missing",
            "tests_run": list(tests_run),
        }
