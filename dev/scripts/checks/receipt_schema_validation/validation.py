"""Per-receipt schema validation logic."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.feature_proof_receipt import (
    FEATURE_PROOF_RECEIPT_SCHEMA_VERSION,
    feature_proof_receipt_from_mapping,
)

from .evidence import evidence_artifact_resolves, is_concrete_pytest_node_id
from .models import (
    FEATURE_PROOF_REQUIRED_FIELDS,
    REASON_INVALID_JSON,
    REASON_INVALID_SCHEMA,
    REASON_MISSING_FIELD,
    REASON_NO_PYTEST_NODE,
    REASON_NOT_MAPPING,
    REASON_UNRESOLVED_ARTIFACT,
    REASON_UNRESOLVED_COMMIT,
    REASON_WRONG_CONTRACT,
    ReceiptSchemaViolation,
)
from .paths import repo_relative


def validate_feature_proof_receipt(
    *,
    path: Path,
    repo_root: Path,
    feature_proof_dir: Path,
    commit_exists: Callable[[str], bool],
) -> tuple[ReceiptSchemaViolation, ...]:
    display_path = str(repo_relative(path, repo_root))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (
            ReceiptSchemaViolation(
                path=display_path,
                reason=REASON_INVALID_JSON,
                detail=f"JSON parse failed: {exc}",
                remediation="Rewrite the receipt through the typed receipt builder.",
            ),
        )
    except OSError as exc:
        return (
            ReceiptSchemaViolation(
                path=display_path,
                reason=REASON_INVALID_JSON,
                detail=f"receipt could not be read: {exc}",
                remediation="Ensure the receipt path is readable or remove the broken artifact.",
            ),
        )
    if not isinstance(payload, Mapping):
        return (
            ReceiptSchemaViolation(
                path=display_path,
                reason=REASON_NOT_MAPPING,
                detail="FeatureProofReceipt payload must be a JSON object.",
                remediation="Rewrite the receipt as a JSON object through the typed builder.",
            ),
        )

    violations: list[ReceiptSchemaViolation] = []
    if payload.get("contract_id") != "FeatureProofReceipt":
        violations.append(
            ReceiptSchemaViolation(
                path=display_path,
                reason=REASON_WRONG_CONTRACT,
                detail=f"contract_id={payload.get('contract_id')!r}",
                remediation="Only FeatureProofReceipt artifacts belong in this directory.",
            )
        )
    if payload.get("schema_version") != FEATURE_PROOF_RECEIPT_SCHEMA_VERSION:
        violations.append(
            ReceiptSchemaViolation(
                path=display_path,
                reason=REASON_INVALID_SCHEMA,
                detail=f"schema_version={payload.get('schema_version')!r}",
                remediation=f"Use schema_version={FEATURE_PROOF_RECEIPT_SCHEMA_VERSION}.",
            )
        )

    missing = sorted(field for field in FEATURE_PROOF_REQUIRED_FIELDS if field not in payload)
    for field in missing:
        violations.append(
            ReceiptSchemaViolation(
                path=display_path,
                reason=REASON_MISSING_FIELD,
                detail=f"missing required field: {field}",
                remediation="Emit the receipt through FeatureProofReceipt so required fields are complete.",
            )
        )

    try:
        receipt = feature_proof_receipt_from_mapping(payload)
    except (TypeError, ValueError) as exc:
        violations.append(
            ReceiptSchemaViolation(
                path=display_path,
                reason=REASON_INVALID_SCHEMA,
                detail=str(exc),
                remediation="Fix the typed FeatureProofReceipt fields or regenerate the receipt.",
            )
        )
        return tuple(violations)

    if not receipt.commit_sha or not commit_exists(receipt.commit_sha):
        violations.append(
            ReceiptSchemaViolation(
                path=display_path,
                reason=REASON_UNRESOLVED_COMMIT,
                detail=f"commit_sha={receipt.commit_sha!r} does not resolve to a local commit",
                remediation="Use an existing commit SHA or add an explicit external-reference receipt.",
            )
        )

    if receipt.real_life_test_status == "proven_passed" and not any(
        is_concrete_pytest_node_id(test_ref) for test_ref in receipt.tests_run
    ):
        violations.append(
            ReceiptSchemaViolation(
                path=display_path,
                reason=REASON_NO_PYTEST_NODE,
                detail="proven_passed requires at least one concrete pytest node id in tests_run",
                remediation="Record the focused pytest node id, not only guard or bundle commands.",
            )
        )

    for artifact in receipt.evidence_artifacts:
        if not evidence_artifact_resolves(
            artifact,
            repo_root=repo_root,
            feature_proof_dir=feature_proof_dir,
        ):
            violations.append(
                ReceiptSchemaViolation(
                    path=display_path,
                    reason=REASON_UNRESOLVED_ARTIFACT,
                    detail=f"evidence_artifact={artifact!r} did not resolve",
                    remediation="Use a real repo path or a supported typed evidence prefix.",
                )
            )
    return tuple(violations)
