"""Shared constants and JSON helpers for governed-exception contracts."""

from __future__ import annotations

from collections.abc import Mapping

GOVERNED_EXCEPTION_SCHEMA_VERSION = 1

GOVERNED_EXCEPTION_LIFECYCLE_CONTRACT_ID = "GovernedExceptionLifecycle"
EXCEPTION_RECEIPT_CONTRACT_ID = "ExceptionReceipt"
RESOLUTION_RECEIPT_CONTRACT_ID = "ResolutionReceipt"
EXCEPTION_POLICY_CONTRACT_ID = "ExceptionPolicy"
EXCEPTION_CLASS_CONTRACT_ID = "ExceptionClass"
EXCEPTION_LIFECYCLE_STATUS_CONTRACT_ID = "ExceptionLifecycleStatus"
CLOSURE_PROOF_CONTRACT_ID = "ClosureProof"
AUTO_REPAIR_RECEIPT_CONTRACT_ID = "AutoRepairReceipt"
MANUAL_BYPASS_IMPORT_RECEIPT_CONTRACT_ID = "ManualBypassImportReceipt"


def json_ready(value: object) -> object:
    """Return a JSON-compatible value for dataclass serialization."""
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    return value


def json_ready_dict(value: object) -> dict[str, object]:
    """Return a JSON-ready mapping payload for dataclass ``to_dict`` methods."""
    payload = json_ready(value)
    if not isinstance(payload, Mapping):
        return {}
    return {str(key): item for key, item in payload.items()}


__all__ = [
    "AUTO_REPAIR_RECEIPT_CONTRACT_ID",
    "CLOSURE_PROOF_CONTRACT_ID",
    "EXCEPTION_CLASS_CONTRACT_ID",
    "EXCEPTION_LIFECYCLE_STATUS_CONTRACT_ID",
    "EXCEPTION_POLICY_CONTRACT_ID",
    "EXCEPTION_RECEIPT_CONTRACT_ID",
    "GOVERNED_EXCEPTION_LIFECYCLE_CONTRACT_ID",
    "GOVERNED_EXCEPTION_SCHEMA_VERSION",
    "MANUAL_BYPASS_IMPORT_RECEIPT_CONTRACT_ID",
    "RESOLUTION_RECEIPT_CONTRACT_ID",
    "json_ready",
    "json_ready_dict",
]
