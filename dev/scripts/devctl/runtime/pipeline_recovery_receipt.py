"""Typed receipt contract for the ``devctl pipeline`` recovery command.

Every recovery action (status is purely read-only) writes one of these
receipts so later sessions can audit how a wedged commit pipeline was
unstuck. The dataclass is intentionally frozen + slotted so the object
behaves like a value type and cannot be mutated mid-action.

Downstream tooling reads the receipt through :func:`to_dict` which
preserves tuple ordering and omits ``None`` fields so JSON consumers
see a stable schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


CONTRACT_ID = "PipelineRecoveryReceipt"
SCHEMA_VERSION = 1

VALID_ACTIONS: tuple[str, ...] = (
    "status",
    "recover",
    "abandon",
    "mark-delivered-local",
    "refresh-authorization",
)


def utc_now_iso() -> str:
    """Return an RFC3339/ISO8601 UTC timestamp suitable for receipts."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass(frozen=True, slots=True)
class PipelineRecoveryReceipt:
    """Typed record of a pipeline recovery action.

    Fields map 1:1 to the JSON surface so tests and operator tooling can
    depend on a single canonical shape. ``previous_state`` / ``new_state``
    stay strings (rather than an enum) because the upstream pipeline
    contract itself carries raw state strings that this command must not
    silently rewrite.
    """

    action: str
    pipeline_id: str
    previous_state: str
    new_state: str
    reason: str
    operator_actor: str
    generated_at_utc: str
    artifact_paths: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = SCHEMA_VERSION
    contract_id: str = CONTRACT_ID

    def __post_init__(self) -> None:
        if self.action not in VALID_ACTIONS:
            raise ValueError(
                f"PipelineRecoveryReceipt.action must be one of "
                f"{VALID_ACTIONS!r}; got {self.action!r}"
            )
        if not self.pipeline_id:
            raise ValueError("PipelineRecoveryReceipt.pipeline_id is required")
        if not self.generated_at_utc:
            raise ValueError(
                "PipelineRecoveryReceipt.generated_at_utc is required"
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dict in a stable field order."""
        return {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "action": self.action,
            "pipeline_id": self.pipeline_id,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "reason": self.reason,
            "operator_actor": self.operator_actor,
            "generated_at_utc": self.generated_at_utc,
            "artifact_paths": list(self.artifact_paths),
        }


def build_receipt(
    *,
    action: str,
    pipeline_id: str,
    previous_state: str,
    new_state: str,
    reason: str,
    operator_actor: str,
    artifact_paths: tuple[str, ...] = (),
    generated_at_utc: str | None = None,
) -> PipelineRecoveryReceipt:
    """Construct a :class:`PipelineRecoveryReceipt` with a filled timestamp."""
    return PipelineRecoveryReceipt(
        action=action,
        pipeline_id=pipeline_id,
        previous_state=previous_state,
        new_state=new_state,
        reason=reason,
        operator_actor=operator_actor,
        generated_at_utc=generated_at_utc or utc_now_iso(),
        artifact_paths=tuple(artifact_paths),
    )
