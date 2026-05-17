"""Typed gate that requires a recent GroundTruthProbeRunReceipt.

Slice 3 of R313 A8: closes the fire-and-forget hole where the
GroundTruthProbeRunReceipt ledger was written but no gate read it before
allowing a final response. This module provides the read-side check that
``final_response_gate`` composes with packet attention and agent-loop blocks.

The reader does not mutate state; it only inspects the latest receipt and
classifies it against typed failure codes. ``require_recent_ground_truth_receipt``
returns ``GroundTruthProbeReceiptCheck`` with ``ok=True`` when the most recent
receipt is satisfied, fresh, and covers the expected trigger paths.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .enum_compat import StrEnum
from .ground_truth_probe_receipt import (
    GroundTruthProbeRunReceipt,
    latest_ground_truth_probe_receipt,
    trigger_paths_digest,
)

GROUND_TRUTH_PROBE_RECEIPT_CHECK_CONTRACT_ID = "GroundTruthProbeReceiptCheck"
GROUND_TRUTH_PROBE_RECEIPT_CHECK_SCHEMA_VERSION = 1
DEFAULT_MAX_RECEIPT_AGE_SECONDS = 900


class GroundTruthProbeReceiptFailureCode(StrEnum):
    """Machine-readable failure codes for the ground-truth receipt gate."""

    OK = "ok"
    GROUND_TRUTH_PROBE_RECEIPT_MISSING = "ground_truth_probe_receipt_missing"
    GROUND_TRUTH_PROBE_RECEIPT_STALE = "ground_truth_probe_receipt_stale"
    GROUND_TRUTH_PROBE_VERDICT_UNSATISFIED = "ground_truth_probe_verdict_unsatisfied"
    GROUND_TRUTH_PROBE_TRIGGER_MISMATCH = "ground_truth_probe_trigger_mismatch"


@dataclass(frozen=True, slots=True)
class GroundTruthProbeReceiptCheck:
    """Result of inspecting the latest ground-truth probe receipt."""

    ok: bool
    failure_code: GroundTruthProbeReceiptFailureCode
    receipt: GroundTruthProbeRunReceipt | None = None
    age_seconds: int = -1
    expected_digest: str = ""
    observed_digest: str = ""
    slice_id: str = ""
    expected_trigger_paths: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = GROUND_TRUTH_PROBE_RECEIPT_CHECK_SCHEMA_VERSION
    contract_id: str = GROUND_TRUTH_PROBE_RECEIPT_CHECK_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "ok": self.ok,
            "failure_code": str(self.failure_code),
            "age_seconds": self.age_seconds,
            "expected_digest": self.expected_digest,
            "observed_digest": self.observed_digest,
            "slice_id": self.slice_id,
            "expected_trigger_paths": list(self.expected_trigger_paths),
            "receipt": self.receipt.to_dict() if self.receipt is not None else None,
        }


def require_recent_ground_truth_receipt(
    *,
    repo_root: Path,
    slice_id: str = "",
    now_utc: datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_RECEIPT_AGE_SECONDS,
    expected_trigger_paths: Iterable[str] = (),
    receipt_path: str | Path | None = None,
) -> GroundTruthProbeReceiptCheck:
    """Return the typed check for the latest ground-truth probe receipt.

    The check is OK when the receipt exists, has verdict ``satisfied``,
    is younger than ``max_age_seconds``, and (if expected trigger paths
    are supplied) its digest matches the digest of the expected paths.
    """
    expected = _normalized_unique(expected_trigger_paths)
    expected_digest = trigger_paths_digest(expected) if expected else ""
    receipt = latest_ground_truth_probe_receipt(
        repo_root=repo_root,
        receipt_path=receipt_path,
    )
    if receipt is None:
        return GroundTruthProbeReceiptCheck(
            ok=False,
            failure_code=GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_RECEIPT_MISSING,
            slice_id=slice_id,
            expected_digest=expected_digest,
            expected_trigger_paths=expected,
        )
    observed_digest = receipt.changed_paths_digest
    now = now_utc if now_utc is not None else datetime.now(tz=timezone.utc)
    age_seconds = _receipt_age_seconds(receipt, now=now)
    if receipt.verdict != "satisfied":
        return GroundTruthProbeReceiptCheck(
            ok=False,
            failure_code=GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_VERDICT_UNSATISFIED,
            receipt=receipt,
            age_seconds=age_seconds,
            expected_digest=expected_digest,
            observed_digest=observed_digest,
            slice_id=slice_id,
            expected_trigger_paths=expected,
        )
    if age_seconds < 0 or age_seconds > max_age_seconds:
        return GroundTruthProbeReceiptCheck(
            ok=False,
            failure_code=GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_RECEIPT_STALE,
            receipt=receipt,
            age_seconds=age_seconds,
            expected_digest=expected_digest,
            observed_digest=observed_digest,
            slice_id=slice_id,
            expected_trigger_paths=expected,
        )
    if expected and observed_digest != expected_digest:
        return GroundTruthProbeReceiptCheck(
            ok=False,
            failure_code=GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_TRIGGER_MISMATCH,
            receipt=receipt,
            age_seconds=age_seconds,
            expected_digest=expected_digest,
            observed_digest=observed_digest,
            slice_id=slice_id,
            expected_trigger_paths=expected,
        )
    return GroundTruthProbeReceiptCheck(
        ok=True,
        failure_code=GroundTruthProbeReceiptFailureCode.OK,
        receipt=receipt,
        age_seconds=age_seconds,
        expected_digest=expected_digest,
        observed_digest=observed_digest,
        slice_id=slice_id,
        expected_trigger_paths=expected,
    )


def _receipt_age_seconds(
    receipt: GroundTruthProbeRunReceipt,
    *,
    now: datetime,
) -> int:
    created = _parse_utc(receipt.created_at_utc)
    if created is None:
        return -1
    delta = now - created
    return int(delta.total_seconds())


def _parse_utc(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalized_unique(values: Iterable[str]) -> tuple[str, ...]:
    rows: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in rows:
            rows.append(text)
    return tuple(sorted(rows))


__all__ = [
    "DEFAULT_MAX_RECEIPT_AGE_SECONDS",
    "GROUND_TRUTH_PROBE_RECEIPT_CHECK_CONTRACT_ID",
    "GROUND_TRUTH_PROBE_RECEIPT_CHECK_SCHEMA_VERSION",
    "GroundTruthProbeReceiptCheck",
    "GroundTruthProbeReceiptFailureCode",
    "require_recent_ground_truth_receipt",
]
