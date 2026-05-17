"""Typed ledger for ArtifactReceipt telemetry from machine-output emitters.

Every devctl CLI invocation that emits compact JSON artifacts (`--format json`)
goes through `runtime.machine_output.emit_machine_artifact_output`, which fires
an in-process `ArtifactReceipt` (`_build_receipt`) keyed on command + delivery
+ sha256. Today that receipt is consumed only by the audit-event pipeline as a
nested mapping; nothing typed-persists the receipt itself as evidence.

This module is the typed sink for those receipts. Each `record_artifact_receipt`
call writes one immutable `ArtifactReceiptRecord` row through the governed
state-store authority. It is fire-and-forget: callers do not block on success,
but the typed row becomes inspectable evidence that a CLI invocation produced
a JSON artifact of a given size/sha256 under a given slice_id/actor.

PII / surface safety:
    The optional ``summary`` mapping from `ArtifactReceipt` may contain
    command-specific values that we do not want to copy into a global ledger
    (paths, IDs, free text). This recorder writes only the SORTED TUPLE OF
    SUMMARY KEYS, never the values. The keys are catalog evidence; the values
    stay inside their owning command's typed artifacts.

composes_with:
    - ``runtime.machine_output._build_receipt`` (producer of the in-process
      ArtifactReceipt this ledger persists).
    - ``runtime.state_store_authority.append_json_mapping`` (governed locked
      writer; the only way rows reach disk).
    - ``audit_events.emit_devctl_audit_event`` (sibling consumer of the same
      `consume_machine_output_metrics` payload).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .state_store_authority import StateStoreWriteResult, append_json_mapping

CONTRACT_ID: str = "ArtifactReceiptRecord"
SCHEMA_VERSION: int = 1
STORE_ID: str = "artifact_receipts"
DEFAULT_ARTIFACT_RECEIPT_STORE_REL: Path = Path("dev/state/artifact_receipts.jsonl")

ALLOWED_DELIVERIES: frozenset[str] = frozenset({"file", "stdout"})


@dataclass(frozen=True, slots=True)
class ArtifactReceiptRecord:
    """One typed row in ``dev/state/artifact_receipts.jsonl``."""

    receipt_id: str
    command: str
    ok: bool
    delivery: str
    artifact_format: str
    artifact_path: str
    size_bytes: int
    estimated_tokens: int
    artifact_sha256: str
    summary_keys: tuple[str, ...]
    slice_id: str
    actor: str
    recorded_at_utc: str
    schema_version: int = SCHEMA_VERSION
    contract_id: str = CONTRACT_ID

    def to_mapping(self) -> dict[str, Any]:
        payload = asdict(self)
        # JSONL rows store summary_keys as a list, not a tuple.
        payload["summary_keys"] = list(self.summary_keys)
        return payload


def _default_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_str(value: object) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _coerce_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _extract_argv_value(argv: Sequence[str], flag: str) -> str:
    """Return the value following ``flag`` in argv, or ``""`` if absent."""
    target = flag
    target_eq = f"{flag}="
    for index, token in enumerate(argv):
        if not isinstance(token, str):
            continue
        if token == target and index + 1 < len(argv):
            candidate = argv[index + 1]
            return candidate if isinstance(candidate, str) else ""
        if token.startswith(target_eq):
            return token[len(target_eq) :]
    return ""


def _compute_receipt_id(
    *,
    command: str,
    artifact_sha256: str,
    recorded_at_utc: str,
) -> str:
    digest = hashlib.sha256()
    digest.update(command.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(artifact_sha256.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(recorded_at_utc.encode("utf-8"))
    return f"art_{digest.hexdigest()[:32]}"


def _summary_keys(summary: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(summary, Mapping) or not summary:
        return ()
    return tuple(sorted(str(key) for key in summary.keys()))


def record_artifact_receipt(
    metrics: Mapping[str, Any],
    *,
    command: str,
    argv: Sequence[str] | None = None,
    ok: bool = True,
    summary: Mapping[str, Any] | None = None,
    repo_root: Path,
    now_utc: Callable[[], str] = _default_now_utc,
    store_rel: Path = DEFAULT_ARTIFACT_RECEIPT_STORE_REL,
) -> StateStoreWriteResult:
    """Persist one typed ArtifactReceiptRecord row.

    Raises:
        ValueError: if ``command`` is empty or the delivery channel is unknown.
        TypeError: if ``metrics`` is not a mapping.
    """
    record = build_artifact_receipt_record(
        metrics,
        command=command,
        argv=argv,
        ok=ok,
        summary=summary,
        now_utc=now_utc,
    )
    return append_artifact_receipt_record(
        record,
        repo_root=repo_root,
        store_rel=store_rel,
    )


def build_artifact_receipt_record(
    metrics: Mapping[str, Any],
    *,
    command: str,
    argv: Sequence[str] | None = None,
    ok: bool = True,
    summary: Mapping[str, Any] | None = None,
    now_utc: Callable[[], str] = _default_now_utc,
) -> ArtifactReceiptRecord:
    """Build the typed ledger row for one machine-output artifact receipt.

    Raises:
        ValueError: if ``command`` is empty or the delivery channel is unknown.
        TypeError: if ``metrics`` is not a mapping.
    """
    if not isinstance(command, str) or not command.strip():
        raise ValueError("artifact receipt requires a non-empty command")
    if not isinstance(metrics, Mapping):
        raise TypeError(
            f"artifact receipt requires Mapping metrics; got {type(metrics).__name__}"
        )

    delivery = _coerce_str(metrics.get("delivery"))
    if delivery not in ALLOWED_DELIVERIES:
        raise ValueError(
            f"artifact receipt delivery must be one of {sorted(ALLOWED_DELIVERIES)};"
            f" got {delivery!r}"
        )

    recorded_at = now_utc()
    artifact_sha = _coerce_str(metrics.get("sha256"))
    receipt_id = _compute_receipt_id(
        command=command,
        artifact_sha256=artifact_sha,
        recorded_at_utc=recorded_at,
    )

    argv_tuple: tuple[str, ...] = tuple(argv or ())
    slice_id = _extract_argv_value(argv_tuple, "--slice-id")
    actor = _extract_argv_value(argv_tuple, "--actor")

    record = ArtifactReceiptRecord(
        receipt_id=receipt_id,
        command=command.strip(),
        ok=bool(ok),
        delivery=delivery,
        artifact_format=_coerce_str(metrics.get("format")),
        artifact_path=_coerce_str(metrics.get("path")),
        size_bytes=_coerce_int(metrics.get("size_bytes")),
        estimated_tokens=_coerce_int(metrics.get("estimated_tokens")),
        artifact_sha256=artifact_sha,
        summary_keys=_summary_keys(summary),
        slice_id=slice_id,
        actor=actor,
        recorded_at_utc=recorded_at,
    )
    return record


def append_artifact_receipt_record(
    record: ArtifactReceiptRecord,
    *,
    repo_root: Path,
    store_rel: Path = DEFAULT_ARTIFACT_RECEIPT_STORE_REL,
) -> StateStoreWriteResult:
    """Append one built ArtifactReceiptRecord to the governed ledger store."""
    store_path = repo_root / store_rel
    return append_json_mapping(
        store_path,
        record.to_mapping(),
        store_id=STORE_ID,
    )


def _parse_recorded_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _row_to_record(row: Mapping[str, Any]) -> ArtifactReceiptRecord | None:
    try:
        summary_keys = tuple(str(k) for k in row.get("summary_keys") or ())
        return ArtifactReceiptRecord(
            receipt_id=_coerce_str(row.get("receipt_id")),
            command=_coerce_str(row.get("command")),
            ok=bool(row.get("ok")),
            delivery=_coerce_str(row.get("delivery")),
            artifact_format=_coerce_str(row.get("artifact_format")),
            artifact_path=_coerce_str(row.get("artifact_path")),
            size_bytes=_coerce_int(row.get("size_bytes")),
            estimated_tokens=_coerce_int(row.get("estimated_tokens")),
            artifact_sha256=_coerce_str(row.get("artifact_sha256")),
            summary_keys=summary_keys,
            slice_id=_coerce_str(row.get("slice_id")),
            actor=_coerce_str(row.get("actor")),
            recorded_at_utc=_coerce_str(row.get("recorded_at_utc")),
            schema_version=_coerce_int(row.get("schema_version")) or SCHEMA_VERSION,
            contract_id=_coerce_str(row.get("contract_id")) or CONTRACT_ID,
        )
    except (TypeError, ValueError):
        return None


def iter_artifact_receipts(
    repo_root: Path,
    *,
    since_seconds: int | None = 86400,
    store_rel: Path = DEFAULT_ARTIFACT_RECEIPT_STORE_REL,
    now_utc: Callable[[], datetime] | None = None,
) -> tuple[ArtifactReceiptRecord, ...]:
    """Yield typed receipt rows from the ledger filtered by recency.

    When ``since_seconds`` is ``None`` all rows are returned. Otherwise rows
    are filtered to those recorded within the trailing window (and rows whose
    ``recorded_at_utc`` cannot be parsed are skipped, never silently kept).
    """
    store_path = repo_root / store_rel
    if not store_path.exists():
        return ()
    cutoff: datetime | None = None
    if since_seconds is not None:
        anchor = now_utc() if now_utc is not None else datetime.now(timezone.utc)
        cutoff = anchor - timedelta(seconds=int(since_seconds))
    records: list[ArtifactReceiptRecord] = []
    for line in store_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, Mapping):
            continue
        record = _row_to_record(payload)
        if record is None:
            continue
        if cutoff is not None:
            parsed = _parse_recorded_at(record.recorded_at_utc)
            if parsed is None or parsed < cutoff:
                continue
        records.append(record)
    return tuple(records)


__all__ = [
    "ALLOWED_DELIVERIES",
    "ArtifactReceiptRecord",
    "CONTRACT_ID",
    "DEFAULT_ARTIFACT_RECEIPT_STORE_REL",
    "SCHEMA_VERSION",
    "STORE_ID",
    "append_artifact_receipt_record",
    "build_artifact_receipt_record",
    "iter_artifact_receipts",
    "record_artifact_receipt",
]
