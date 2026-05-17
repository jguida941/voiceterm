"""Typed contracts for asynchronous remote validation evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Literal

from ..runtime.value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)


REMOTE_VALIDATION_RECEIPT_CONTRACT_ID = "RemoteValidationReceipt"
REMOTE_VALIDATION_RECEIPT_SCHEMA_VERSION = 1

RemoteValidationStatus = Literal[
    "queued",
    "running",
    "completed_green",
    "completed_failed",
    "completed_stale",
    "expired",
    "superseded",
    "artifact_missing",
    "ingestion_failed",
]
RemoteEvidenceFreshness = Literal[
    "current",
    "stale_but_relevant",
    "stale_and_superseded",
    "unknown",
]
AffectedPathPresence = Literal["present", "absent", "moved"]


@dataclass(frozen=True, slots=True)
class RemoteValidationReceipt:
    """Cloud or remote-check evidence reconciled back to the local tree."""

    receipt_id: str
    status: RemoteValidationStatus
    applies_to_tree: str
    current_tree: str
    freshness: RemoteEvidenceFreshness
    failed_checks: tuple[str, ...] = ()
    recommended_next_action: tuple[str, ...] = ()
    blocked_actions: tuple[str, ...] = ()
    artifact_bundle_ref: str = ""
    plan_row_id: str = ""
    schema_version: int = REMOTE_VALIDATION_RECEIPT_SCHEMA_VERSION
    contract_id: str = REMOTE_VALIDATION_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["failed_checks"] = list(self.failed_checks)
        payload["recommended_next_action"] = list(self.recommended_next_action)
        payload["blocked_actions"] = list(self.blocked_actions)
        return payload


def remote_validation_receipt_from_mapping(
    payload: Mapping[str, object],
) -> RemoteValidationReceipt:
    """Normalize a mapping into a RemoteValidationReceipt."""
    mapping = coerce_mapping(payload)
    return RemoteValidationReceipt(
        schema_version=coerce_int(mapping.get("schema_version"))
        or REMOTE_VALIDATION_RECEIPT_SCHEMA_VERSION,
        contract_id=coerce_string(mapping.get("contract_id"))
        or REMOTE_VALIDATION_RECEIPT_CONTRACT_ID,
        receipt_id=coerce_string(mapping.get("receipt_id")),
        status=_coerce_status(mapping.get("status")),
        applies_to_tree=coerce_string(mapping.get("applies_to_tree")),
        current_tree=coerce_string(mapping.get("current_tree")),
        freshness=_coerce_freshness(mapping.get("freshness")),
        failed_checks=coerce_string_items(mapping.get("failed_checks")),
        recommended_next_action=coerce_string_items(
            mapping.get("recommended_next_action")
            or mapping.get("recommended_next_actions")
        ),
        blocked_actions=coerce_string_items(mapping.get("blocked_actions")),
        artifact_bundle_ref=coerce_string(mapping.get("artifact_bundle_ref")),
        plan_row_id=coerce_string(mapping.get("plan_row_id")),
    )


def _coerce_status(value: object) -> RemoteValidationStatus:
    text = coerce_string(value)
    allowed = RemoteValidationStatus.__args__
    if text in allowed:
        return text  # type: ignore[return-value]
    return "queued"


def _coerce_freshness(value: object) -> RemoteEvidenceFreshness:
    text = coerce_string(value)
    allowed = RemoteEvidenceFreshness.__args__
    if text in allowed:
        return text  # type: ignore[return-value]
    return "unknown"


__all__ = [
    "AffectedPathPresence",
    "REMOTE_VALIDATION_RECEIPT_CONTRACT_ID",
    "REMOTE_VALIDATION_RECEIPT_SCHEMA_VERSION",
    "RemoteEvidenceFreshness",
    "RemoteValidationReceipt",
    "RemoteValidationStatus",
    "remote_validation_receipt_from_mapping",
]
