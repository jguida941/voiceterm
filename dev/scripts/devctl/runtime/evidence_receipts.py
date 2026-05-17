"""Contract constants for evidence-only receipt artifacts."""

from __future__ import annotations

from dataclasses import dataclass

DOGFOOD_SELF_CHECK_RECEIPT_CONTRACT_ID = "DogfoodSelfCheckReceipt"
DOGFOOD_SELF_CHECK_RECEIPT_SCHEMA_VERSION = 1
REVIEWER_AUDIT_RECEIPT_CONTRACT_ID = "ReviewerAuditReceipt"
REVIEWER_AUDIT_RECEIPT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class TokenOptimizationDogfoodReceipt:
    receipt_id: str
    optimization_id: str
    feature_lifecycle_proof_id: str
    dogfood_record_id: str
    dogfood_round_ref: str
    before_token_count: int
    after_token_count: int
    capability_preserved_checks: tuple[str, ...]
    context_preserved_checks: tuple[str, ...]
    actor_ids: tuple[str, ...]
    status: str
    schema_version: int = 1
    contract_id: str = "TokenOptimizationDogfoodReceipt"


__all__ = [
    "DOGFOOD_SELF_CHECK_RECEIPT_CONTRACT_ID",
    "DOGFOOD_SELF_CHECK_RECEIPT_SCHEMA_VERSION",
    "REVIEWER_AUDIT_RECEIPT_CONTRACT_ID",
    "REVIEWER_AUDIT_RECEIPT_SCHEMA_VERSION",
    "TokenOptimizationDogfoodReceipt",
]
