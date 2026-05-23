"""Typed records and reason constants for the coverage-sweep guard."""

from __future__ import annotations

from dataclasses import asdict, dataclass


COMMAND = "check_receipt_store_coverage_sweep"
CONTRACT_ID = "ReceiptStoreCoverageSweepGuard"

REASON_MISSING_CLASSIFICATION = "receipt_store_missing_coverage_classification"
REASON_NO_WRITER = "receipt_store_without_named_writer"
REASON_NO_READER = "receipt_store_without_active_consumer"
REASON_NO_SCHEMA_GUARD = "receipt_store_without_schema_guard"
REASON_UNRESOLVED_SCHEMA_GUARD_REF = "receipt_store_schema_guard_ref_unresolved"
REASON_NO_PROVENANCE = "receipt_store_without_provenance_or_archive_disposition"

DISPLAY_TEXT = (
    "AI DUMBASS ALERT: receipt store coverage gap. Receipt stores must name a "
    "writer, reader, schema guard, and provenance or archive disposition."
)


@dataclass(frozen=True, slots=True)
class ReceiptStoreCoverage:
    store_path: str
    writer_refs: tuple[str, ...]
    reader_refs: tuple[str, ...]
    schema_guard_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...] = ()
    archive_disposition_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        for key in (
            "writer_refs",
            "reader_refs",
            "schema_guard_refs",
            "provenance_refs",
            "archive_disposition_refs",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class ReceiptStoreCoverageViolation:
    store_path: str
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
