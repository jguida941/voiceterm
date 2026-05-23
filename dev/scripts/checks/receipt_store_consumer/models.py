"""Typed records and reason constants for the receipt-store consumer guard."""

from __future__ import annotations

from dataclasses import asdict, dataclass


COMMAND = "check_receipt_store_has_active_consumer"
CONTRACT_ID = "ReceiptStoreHasActiveConsumerGuard"

REASON_MISSING_CLASSIFICATION = "receipt_store_missing_consumer_classification"
REASON_NO_READER = "receipt_store_without_active_consumer"
REASON_NO_WRITER = "receipt_store_without_named_writer"

DISPLAY_TEXT = (
    "AI DUMBASS ALERT: receipt store has no active consumer. Receipt stores "
    "must name a writer and reader, or carry an explicit evidence-only disposition."
)


@dataclass(frozen=True, slots=True)
class ReceiptStoreClassification:
    store_path: str
    writer_refs: tuple[str, ...]
    reader_refs: tuple[str, ...]
    disposition: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["writer_refs"] = list(self.writer_refs)
        payload["reader_refs"] = list(self.reader_refs)
        return payload


@dataclass(frozen=True, slots=True)
class ReceiptStoreViolation:
    store_path: str
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
