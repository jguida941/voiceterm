"""Per-classification violation logic for the coverage-sweep guard."""

from __future__ import annotations

from pathlib import Path

from .models import (
    REASON_NO_PROVENANCE,
    REASON_NO_READER,
    REASON_NO_SCHEMA_GUARD,
    REASON_NO_WRITER,
    REASON_UNRESOLVED_SCHEMA_GUARD_REF,
    ReceiptStoreCoverage,
    ReceiptStoreCoverageViolation,
)


def violations_for_classification(
    classification: ReceiptStoreCoverage,
    *,
    repo_root: Path,
) -> tuple[ReceiptStoreCoverageViolation, ...]:
    violations: list[ReceiptStoreCoverageViolation] = []
    if not classification.writer_refs:
        violations.append(
            ReceiptStoreCoverageViolation(
                store_path=classification.store_path,
                reason=REASON_NO_WRITER,
                detail="store has no named writer_refs",
                remediation="Name the canonical writer seam or quarantine the store.",
            )
        )
    if not classification.reader_refs:
        violations.append(
            ReceiptStoreCoverageViolation(
                store_path=classification.store_path,
                reason=REASON_NO_READER,
                detail="store has no named reader_refs",
                remediation="Name the active consumer before selectors or gates trust this store.",
            )
        )
    if not classification.schema_guard_refs:
        violations.append(
            ReceiptStoreCoverageViolation(
                store_path=classification.store_path,
                reason=REASON_NO_SCHEMA_GUARD,
                detail="store has no schema_guard_refs",
                remediation="Add a schema guard or point to the existing guard that validates this store.",
            )
        )
    for schema_guard_ref in classification.schema_guard_refs:
        if schema_guard_ref_is_unresolved(schema_guard_ref, repo_root=repo_root):
            violations.append(
                ReceiptStoreCoverageViolation(
                    store_path=classification.store_path,
                    reason=REASON_UNRESOLVED_SCHEMA_GUARD_REF,
                    detail=f"schema_guard_ref does not resolve: {schema_guard_ref}",
                    remediation="Use an existing guard path or classify the store as pending coverage.",
                )
            )
    if not classification.provenance_refs and not classification.archive_disposition_refs:
        violations.append(
            ReceiptStoreCoverageViolation(
                store_path=classification.store_path,
                reason=REASON_NO_PROVENANCE,
                detail="store has neither provenance_refs nor archive_disposition_refs",
                remediation="Attach ingestion/proof provenance or an explicit archive disposition.",
            )
        )
    return tuple(violations)


def schema_guard_ref_is_unresolved(ref: str, *, repo_root: Path) -> bool:
    text = ref.strip()
    if not text.startswith("dev/"):
        return False
    return not (repo_root / text).exists()
