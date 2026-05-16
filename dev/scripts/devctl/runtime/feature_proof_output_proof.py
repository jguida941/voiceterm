"""Non-trivial output-proof checks for FeatureProofReceipt artifacts."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .feature_proof_receipt import (
    FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT,
    FEATURE_PROOF_RECEIPT_SCHEMA_VERSION,
    FeatureProofReceipt,
    feature_proof_receipt_artifact_relpath,
    write_feature_proof_receipt_artifact,
)
from .feature_proof_role_review import role_review_terminal_coverage_failure_reasons
from .value_coercion import coerce_string

NON_TRIVIAL_OUTPUT_PROOF_CONTRACT_ID = "NonTrivialOutputProof"
NON_TRIVIAL_OUTPUT_PROOF_SCHEMA_VERSION = FEATURE_PROOF_RECEIPT_SCHEMA_VERSION
NON_TRIVIAL_OUTPUT_PROOF_FINDING_CONTRACT_ID = (
    "NonTrivialOutputProofRemediationFinding"
)
NON_TRIVIAL_OUTPUT_PROOF_LEDGER_CONTRACT_ID = (
    "NonTrivialOutputProofRemediationFindingLedger"
)
ROLE_REVIEW_COMPLETED_FINDING_CONTRACT_ID = (
    "RoleReviewCompletedRemediationFinding"
)


@dataclass(frozen=True, slots=True)
class NonTrivialOutputProof:
    ref_resolves: bool
    has_real_tests: bool
    not_circular: bool
    role_review_terminal_refs_present: bool
    failure_reasons: tuple[str, ...]
    schema_version: int = NON_TRIVIAL_OUTPUT_PROOF_SCHEMA_VERSION
    contract_id: str = NON_TRIVIAL_OUTPUT_PROOF_CONTRACT_ID

    @property
    def ok(self) -> bool:
        return (
            self.ref_resolves
            and self.has_real_tests
            and self.not_circular
            and self.role_review_terminal_refs_present
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["failure_reasons"] = list(self.failure_reasons)
        return payload


@dataclass(frozen=True, slots=True)
class NonTrivialOutputProofRemediationFinding:
    finding_id: str
    feature_proof_receipt_path: str
    commit_sha: str
    feature_id: str
    failure_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    emitted_at_utc: str = ""
    remediation_status: str = "open"
    schema_version: int = NON_TRIVIAL_OUTPUT_PROOF_SCHEMA_VERSION
    contract_id: str = NON_TRIVIAL_OUTPUT_PROOF_FINDING_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["failure_reasons"] = list(self.failure_reasons)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class NonTrivialOutputProofRemediationFindingLedger:
    ledger_path: str
    finding_contract_id: str = NON_TRIVIAL_OUTPUT_PROOF_FINDING_CONTRACT_ID
    storage_format: str = "jsonl"
    schema_version: int = NON_TRIVIAL_OUTPUT_PROOF_SCHEMA_VERSION
    contract_id: str = NON_TRIVIAL_OUTPUT_PROOF_LEDGER_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RoleReviewCompletedRemediationFinding:
    finding_id: str
    feature_proof_receipt_path: str
    commit_sha: str
    feature_id: str
    failure_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    emitted_at_utc: str = ""
    schema_version: int = NON_TRIVIAL_OUTPUT_PROOF_SCHEMA_VERSION
    contract_id: str = ROLE_REVIEW_COMPLETED_FINDING_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["failure_reasons"] = list(self.failure_reasons)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


def validate_non_trivial_output_proof(
    fpr: FeatureProofReceipt,
    *,
    repo_root: Path | str | None = None,
    receipt_path: Path | str | None = None,
) -> NonTrivialOutputProof:
    """Validate that a FeatureProofReceipt cites substantive proof."""
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    evidence_refs = _feature_proof_evidence_refs(fpr)
    unresolved = tuple(
        ref for ref in evidence_refs if not _feature_proof_ref_resolves(root, ref)
    )
    circular = tuple(
        ref
        for ref in evidence_refs
        if _is_circular_feature_proof_ref(root, ref, fpr=fpr, receipt_path=receipt_path)
    )
    role_review_failures = role_review_terminal_coverage_failure_reasons(fpr)
    has_real_tests = any("::" in item for item in fpr.tests_run)
    failure_reasons: list[str] = []
    failure_reasons.extend(f"ref_unresolved:{ref}" for ref in unresolved)
    if not has_real_tests:
        failure_reasons.append("no_real_tests")
    failure_reasons.extend(f"circular_ref:{ref}" for ref in circular)
    failure_reasons.extend(role_review_failures)
    return NonTrivialOutputProof(
        ref_resolves=not unresolved,
        has_real_tests=has_real_tests,
        not_circular=not circular,
        role_review_terminal_refs_present=not role_review_failures,
        failure_reasons=tuple(dict.fromkeys(failure_reasons)),
    )


def require_non_circular_resolved_output_refs(
    fpr: FeatureProofReceipt,
    *,
    repo_root: Path | str | None = None,
    receipt_path: Path | str | None = None,
    require_real_tests: bool = False,
) -> NonTrivialOutputProof:
    """Fail if a new FPR would ship with unresolved or circular evidence refs."""
    proof = validate_non_trivial_output_proof(
        fpr,
        repo_root=repo_root,
        receipt_path=receipt_path,
    )
    blocking = (
        proof.failure_reasons
        if require_real_tests
        else tuple(
            reason
            for reason in proof.failure_reasons
            if reason.startswith("ref_unresolved:")
            or reason.startswith("circular_ref:")
            or reason.startswith("missing_role_review_terminal_ref:")
        )
    )
    if blocking:
        raise ValueError(
            "non_trivial_output_proof_ref_failure:" + ",".join(blocking)
        )
    return proof


def write_validated_feature_proof_receipt_artifact(
    repo_root: Path,
    receipt: FeatureProofReceipt,
    *,
    receipt_path: Path | str | None = None,
    require_real_tests: bool = False,
) -> str:
    require_non_circular_resolved_output_refs(
        receipt,
        repo_root=repo_root,
        receipt_path=receipt_path,
        require_real_tests=require_real_tests,
    )
    return write_feature_proof_receipt_artifact(repo_root, receipt)


def _feature_proof_evidence_refs(fpr: FeatureProofReceipt) -> tuple[str, ...]:
    refs = (fpr.dogfood_invocation_evidence_ref, *fpr.evidence_artifacts)
    return tuple(ref for ref in (coerce_string(value) for value in refs) if ref)


def _ref_filesystem_path(repo_root: Path, ref: str) -> str:
    text = coerce_string(ref).strip()
    if text.startswith("path:"):
        text = text.removeprefix("path:")
    if "::" in text:
        text = text.split("::", 1)[0]
    path = Path(text)
    if not path.is_absolute():
        path = repo_root / path
    return os.fspath(path)


def _feature_proof_ref_resolves(repo_root: Path, ref: str) -> bool:
    return os.path.exists(_ref_filesystem_path(repo_root, ref))


def _is_circular_feature_proof_ref(
    repo_root: Path,
    ref: str,
    *,
    fpr: FeatureProofReceipt,
    receipt_path: Path | str | None,
) -> bool:
    text = coerce_string(ref).strip()
    if text.startswith("path:"):
        text = text.removeprefix("path:")
    if not text:
        return False
    own_relpath = feature_proof_receipt_artifact_relpath(fpr.commit_sha)
    circular_roots = (
        FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT,
        FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT + "/",
        own_relpath,
    )
    if text in circular_roots:
        return True
    ref_path = Path(text)
    if not ref_path.is_absolute():
        ref_path = repo_root / ref_path
    ref_resolved = ref_path.resolve(strict=False)
    feature_root = (repo_root / FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT).resolve(
        strict=False
    )
    if ref_resolved == feature_root:
        return True
    own_path = (repo_root / own_relpath).resolve(strict=False)
    if ref_resolved == own_path:
        return True
    if receipt_path is not None:
        path = Path(receipt_path)
        if not path.is_absolute():
            path = repo_root / path
        if ref_resolved == path.resolve(strict=False):
            return True
    return False


__all__ = [
    "NON_TRIVIAL_OUTPUT_PROOF_CONTRACT_ID",
    "NON_TRIVIAL_OUTPUT_PROOF_FINDING_CONTRACT_ID",
    "NON_TRIVIAL_OUTPUT_PROOF_LEDGER_CONTRACT_ID",
    "NON_TRIVIAL_OUTPUT_PROOF_SCHEMA_VERSION",
    "ROLE_REVIEW_COMPLETED_FINDING_CONTRACT_ID",
    "NonTrivialOutputProof",
    "NonTrivialOutputProofRemediationFinding",
    "NonTrivialOutputProofRemediationFindingLedger",
    "RoleReviewCompletedRemediationFinding",
    "require_non_circular_resolved_output_refs",
    "validate_non_trivial_output_proof",
    "write_validated_feature_proof_receipt_artifact",
]
