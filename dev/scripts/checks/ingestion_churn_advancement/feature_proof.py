"""Feature-proof receipt loading helpers for the ingestion-churn guard."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path


def feature_proof_row_ids(root: Path) -> frozenset[str]:
    row_ids: set[str] = set()
    if not root.exists():
        return frozenset()
    for path in sorted(root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        if payload.get("contract_id") != "FeatureProofReceipt":
            continue
        if payload.get("real_life_test_status") != "proven_passed":
            continue
        for row_id in feature_proof_row_refs(payload):
            row_ids.add(row_id)
    return frozenset(row_ids)


def feature_proof_row_refs(payload: Mapping[str, object]) -> tuple[str, ...]:
    refs: list[str] = []
    for field in ("plan_row_id", "row_id", "feature_id", "target_ref"):
        value = str(payload.get(field, "") or "").strip()
        if value:
            refs.append(value)
    for field in (
        "plan_row_ids",
        "plan_refs",
        "evidence_artifacts",
        "role_review_receipt_refs",
        "bypass_audit_trail_refs",
    ):
        sequence = payload.get(field)
        if not isinstance(sequence, Sequence) or isinstance(sequence, (str, bytes)):
            continue
        refs.extend(str(item) for item in sequence if str(item).strip())
    return tuple(refs)
