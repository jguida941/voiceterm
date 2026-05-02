"""Read-side projection helpers for local pipeline-delivery receipts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .pipeline_recovery_receipt import CONTRACT_ID as RECOVERY_RECEIPT_CONTRACT_ID
from .remote_commit_pipeline_state import STATE_DELIVERED_LOCALLY_PENDING_PUBLISH
from .value_coercion import coerce_string, coerce_string_items


LOCAL_DELIVERY_RECEIPT_FILENAME = "pipeline_local_delivery_receipt.json"
LOCAL_DELIVERY_ACTION = "mark-delivered-local"


def apply_local_delivery_receipt(
    payload: Mapping[str, object],
    *,
    receipts_root: Path,
    pipeline_path: Path | None = None,
) -> dict[str, Any]:
    """Overlay a matching local-delivery receipt onto a pipeline payload.

    Recovery actions write receipts outside the event stream. Projection
    refreshes may later regenerate ``commit_pipeline.json`` from older event
    state, so readers must treat a matching local-delivery receipt as the
    newest durable pipeline lifecycle fact.
    """
    pipeline = dict(payload)
    receipt_path = receipts_root / LOCAL_DELIVERY_RECEIPT_FILENAME
    receipt = _load_receipt(receipt_path)
    if not _receipt_matches_pipeline(
        receipt,
        pipeline=pipeline,
        pipeline_path=pipeline_path,
    ):
        return pipeline

    pipeline["state"] = STATE_DELIVERED_LOCALLY_PENDING_PUBLISH
    pipeline["blocked_reason"] = ""
    pipeline["recovery_action_allowed"] = ""
    pipeline["local_delivery_receipt_path"] = str(receipt_path)
    pipeline["local_delivery_reason"] = coerce_string(receipt.get("reason"))
    pipeline["delivered_at_utc"] = coerce_string(receipt.get("generated_at_utc"))
    pipeline["delivered_by"] = coerce_string(receipt.get("operator_actor"))
    return pipeline


def _load_receipt(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _receipt_matches_pipeline(
    receipt: Mapping[str, object],
    *,
    pipeline: Mapping[str, object],
    pipeline_path: Path | None,
) -> bool:
    if not receipt:
        return False
    if coerce_string(receipt.get("contract_id")) != RECOVERY_RECEIPT_CONTRACT_ID:
        return False
    if coerce_string(receipt.get("action")) != LOCAL_DELIVERY_ACTION:
        return False
    if coerce_string(receipt.get("new_state")) != STATE_DELIVERED_LOCALLY_PENDING_PUBLISH:
        return False
    receipt_pipeline_id = coerce_string(receipt.get("pipeline_id"))
    pipeline_id = coerce_string(pipeline.get("pipeline_id"))
    if not receipt_pipeline_id or receipt_pipeline_id != pipeline_id:
        return False
    previous_state = coerce_string(receipt.get("previous_state"))
    current_state = coerce_string(pipeline.get("state"))
    if current_state == STATE_DELIVERED_LOCALLY_PENDING_PUBLISH:
        return True
    if previous_state and current_state and previous_state != current_state:
        return False
    if pipeline_path is None:
        return True
    expected_path = str(pipeline_path.resolve())
    artifact_paths = coerce_string_items(receipt.get("artifact_paths"))
    resolved_artifact_paths = {str(Path(path).resolve()) for path in artifact_paths}
    return not resolved_artifact_paths or expected_path in resolved_artifact_paths


__all__ = [
    "LOCAL_DELIVERY_ACTION",
    "LOCAL_DELIVERY_RECEIPT_FILENAME",
    "apply_local_delivery_receipt",
]
