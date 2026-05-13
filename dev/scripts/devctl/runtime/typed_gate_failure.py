"""Typed discoverability payload for governance gate failures."""

from __future__ import annotations

from dataclasses import asdict, dataclass


TYPED_GATE_FAILURE_CONTRACT_ID = "TypedGateFailure"
TYPED_GATE_FAILURE_SCHEMA_VERSION = 1
DEFAULT_BYPASS_RECEIPT_KIND = "BypassReceipt"
DEFAULT_EXCEPTION_LIFECYCLE_CLASS = "GovernedExceptionLifecycle"


@dataclass(frozen=True, slots=True)
class TypedGateFailure:
    """Machine-readable gate failure with the existing typed escape path."""

    gate_id: str
    violation_reason: str
    bypass_invocation: str
    bypass_receipt_kind: str = DEFAULT_BYPASS_RECEIPT_KIND
    contract_definition_path: str = ""
    exception_lifecycle_class: str = DEFAULT_EXCEPTION_LIFECYCLE_CLASS
    schema_version: int = TYPED_GATE_FAILURE_SCHEMA_VERSION
    contract_id: str = TYPED_GATE_FAILURE_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def typed_gate_failure_dict(failure: TypedGateFailure | None) -> dict[str, object]:
    """Return a JSON-ready dict while keeping absent failures compact."""
    return failure.to_dict() if failure is not None else {}


__all__ = [
    "DEFAULT_BYPASS_RECEIPT_KIND",
    "DEFAULT_EXCEPTION_LIFECYCLE_CLASS",
    "TYPED_GATE_FAILURE_CONTRACT_ID",
    "TYPED_GATE_FAILURE_SCHEMA_VERSION",
    "TypedGateFailure",
    "typed_gate_failure_dict",
]
