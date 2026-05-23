"""Typed records and reason constants for the receipt-schema validation guard."""

from __future__ import annotations

from dataclasses import asdict, dataclass

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT


COMMAND = "check_receipt_schema_validation"
CONTRACT_ID = "ReceiptSchemaValidationGuard"
DEFAULT_FEATURE_PROOF_DIR = REPO_ROOT / "dev/reports/feature_proof_receipts"

REASON_INVALID_JSON = "receipt_invalid_json"
REASON_NOT_MAPPING = "receipt_payload_not_object"
REASON_WRONG_CONTRACT = "feature_proof_receipt_wrong_contract"
REASON_MISSING_FIELD = "feature_proof_receipt_missing_required_field"
REASON_INVALID_SCHEMA = "feature_proof_receipt_invalid_schema"
REASON_UNRESOLVED_COMMIT = "feature_proof_receipt_unresolved_commit_sha"
REASON_NO_PYTEST_NODE = "feature_proof_receipt_proven_passed_without_pytest_node"
REASON_UNRESOLVED_ARTIFACT = "feature_proof_receipt_unresolved_evidence_artifact"

DISPLAY_TEXT = (
    "AI DUMBASS ALERT: receipt schema violation. Receipt-store writes are not "
    "authority unless their schema, commit anchor, tests, and evidence resolve."
)

FEATURE_PROOF_REQUIRED_FIELDS = frozenset(
    {
        "contract_id",
        "schema_version",
        "feature_id",
        "commit_sha",
        "implementer_actor",
        "review_fleet_roles_ran",
        "review_fleet_actor",
        "tests_run",
        "tests_passed_count",
        "tests_failed_count",
        "connectivity_guards_ran",
        "connectivity_guards_passed",
        "dogfood_invocation_evidence_ref",
        "real_life_test_status",
        "not_tested_rationale",
        "bypass_audit_trail_refs",
        "proven_at_utc",
        "evidence_artifacts",
    }
)

TYPED_EVIDENCE_PREFIXES = frozenset(
    {
        "action_result",
        "ancestor_feature_proof_receipt",
        "bypass",
        "command_output",
        "finding",
        "inline",
        "operator_role_assignment",
        "packet",
        "plan-ingest",
        "plan-source",
        "role_review",
        "test",
        "validation_bundle",
    }
)


@dataclass(frozen=True, slots=True)
class ReceiptSchemaViolation:
    path: str
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
