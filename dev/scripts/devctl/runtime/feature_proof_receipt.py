"""Typed per-feature proof receipt artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import ClassVar, Literal, cast

from .value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)

FEATURE_PROOF_RECEIPT_CONTRACT_ID = "FeatureProofReceipt"
FEATURE_PROOF_RECEIPT_SCHEMA_VERSION = 1
FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT = "dev/reports/feature_proof_receipts"

RealLifeTestStatus = Literal[
    "proven_passed",
    "proven_failed",
    "not_tested_with_rationale",
]

_VALID_REAL_LIFE_TEST_STATUSES = {
    "proven_passed",
    "proven_failed",
    "not_tested_with_rationale",
}


@dataclass(frozen=True, slots=True)
class FeatureProofReceipt:
    """Operator-facing proof bundle for a shipped feature commit."""

    contract_id: ClassVar[str] = FEATURE_PROOF_RECEIPT_CONTRACT_ID
    schema_version: ClassVar[int] = FEATURE_PROOF_RECEIPT_SCHEMA_VERSION

    feature_id: str
    commit_sha: str
    implementer_actor: str
    review_fleet_roles_ran: tuple[str, ...]
    review_fleet_actor: str
    tests_run: tuple[str, ...]
    tests_passed_count: int
    tests_failed_count: int
    connectivity_guards_ran: tuple[str, ...]
    connectivity_guards_passed: bool
    dogfood_invocation_evidence_ref: str
    real_life_test_status: RealLifeTestStatus
    not_tested_rationale: str | None
    bypass_audit_trail_refs: tuple[str, ...]
    proven_at_utc: str
    evidence_artifacts: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.real_life_test_status not in _VALID_REAL_LIFE_TEST_STATUSES:
            raise ValueError(
                f"invalid real_life_test_status: {self.real_life_test_status!r}"
            )
        if self.real_life_test_status == "not_tested_with_rationale":
            if not coerce_string(self.not_tested_rationale):
                raise ValueError(
                    "not_tested_rationale is required when real_life_test_status "
                    "is not_tested_with_rationale"
                )
        if self.tests_passed_count < 0 or self.tests_failed_count < 0:
            raise ValueError("test counts must be non-negative")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["contract_id"] = self.contract_id
        payload["schema_version"] = self.schema_version
        payload["review_fleet_roles_ran"] = list(self.review_fleet_roles_ran)
        payload["tests_run"] = list(self.tests_run)
        payload["connectivity_guards_ran"] = list(self.connectivity_guards_ran)
        payload["bypass_audit_trail_refs"] = list(self.bypass_audit_trail_refs)
        payload["evidence_artifacts"] = list(self.evidence_artifacts)
        return payload


def feature_proof_receipt_from_mapping(
    payload: Mapping[str, object],
) -> FeatureProofReceipt:
    """Normalize a mapping into a FeatureProofReceipt."""
    mapping = coerce_mapping(payload)
    return FeatureProofReceipt(
        feature_id=coerce_string(mapping.get("feature_id")),
        commit_sha=coerce_string(mapping.get("commit_sha")),
        implementer_actor=coerce_string(mapping.get("implementer_actor")),
        review_fleet_roles_ran=coerce_string_items(
            mapping.get("review_fleet_roles_ran")
        ),
        review_fleet_actor=coerce_string(mapping.get("review_fleet_actor")),
        tests_run=coerce_string_items(mapping.get("tests_run")),
        tests_passed_count=coerce_int(mapping.get("tests_passed_count")),
        tests_failed_count=coerce_int(mapping.get("tests_failed_count")),
        connectivity_guards_ran=coerce_string_items(
            mapping.get("connectivity_guards_ran")
        ),
        connectivity_guards_passed=bool(mapping.get("connectivity_guards_passed")),
        dogfood_invocation_evidence_ref=coerce_string(
            mapping.get("dogfood_invocation_evidence_ref")
        ),
        real_life_test_status=_coerce_real_life_test_status(
            mapping.get("real_life_test_status")
        ),
        not_tested_rationale=_coerce_optional_string(
            mapping.get("not_tested_rationale")
        ),
        bypass_audit_trail_refs=coerce_string_items(
            mapping.get("bypass_audit_trail_refs")
        ),
        proven_at_utc=coerce_string(mapping.get("proven_at_utc")),
        evidence_artifacts=coerce_string_items(mapping.get("evidence_artifacts")),
    )


def feature_proof_receipt_artifact_relpath(commit_sha: str) -> str:
    """Return the repo-relative artifact path for one FeatureProofReceipt."""
    token = _path_token(commit_sha) or "unknown"
    return f"{FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT}/{token}.json"


def write_feature_proof_receipt_artifact(
    repo_root: Path,
    receipt: FeatureProofReceipt,
) -> str:
    """Materialize a FeatureProofReceipt artifact and return its relpath."""
    relpath = feature_proof_receipt_artifact_relpath(receipt.commit_sha)
    path = repo_root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n")
    return relpath


def _coerce_real_life_test_status(value: object) -> RealLifeTestStatus:
    status = coerce_string(value)
    if status not in _VALID_REAL_LIFE_TEST_STATUSES:
        raise ValueError(f"invalid real_life_test_status: {status!r}")
    return cast(RealLifeTestStatus, status)


def _coerce_optional_string(value: object) -> str | None:
    text = coerce_string(value)
    return text if text else None


def _path_token(value: str) -> str:
    text = coerce_string(value)
    return "".join(char for char in text if char.isalnum() or char in "._-")[:80]


__all__ = [
    "FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT",
    "FEATURE_PROOF_RECEIPT_CONTRACT_ID",
    "FEATURE_PROOF_RECEIPT_SCHEMA_VERSION",
    "FeatureProofReceipt",
    "RealLifeTestStatus",
    "feature_proof_receipt_artifact_relpath",
    "feature_proof_receipt_from_mapping",
    "write_feature_proof_receipt_artifact",
]
