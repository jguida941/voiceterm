"""Typed contracts for durable evidence archive planning."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .value_coercion import coerce_bool, coerce_int, coerce_string, coerce_string_items

EVIDENCE_ARCHIVE_POLICY_CONTRACT_ID = "EvidenceArchivePolicy"
EVIDENCE_ARCHIVE_MANIFEST_CONTRACT_ID = "EvidenceArchiveManifest"
EVIDENCE_ARCHIVE_RECEIPT_CONTRACT_ID = "EvidenceArchiveReceipt"
EVIDENCE_ARCHIVE_SCHEMA_VERSION = 1
DEFAULT_EVIDENCE_RETENTION_DAYS = 30
DEFAULT_EVIDENCE_ARCHIVE_ROOT = "dev/reports/archive"
DEFAULT_EVIDENCE_ARCHIVE_COMPRESSION = "zstd"
ARCHIVE_ELIGIBLE_LIFECYCLE_STATUSES = ("closed", "resolved")
EVIDENCE_ARCHIVE_REF_PREFIX = "evidence_archive:"


@dataclass(frozen=True, slots=True)
class EvidenceArchivePolicy:
    """Retention policy for one family of typed evidence artifacts."""

    policy_id: str
    evidence_kind: str
    retention_days: int = DEFAULT_EVIDENCE_RETENTION_DAYS
    archive_root: str = DEFAULT_EVIDENCE_ARCHIVE_ROOT
    compression: str = DEFAULT_EVIDENCE_ARCHIVE_COMPRESSION
    archive_after_lifecycle_statuses: tuple[str, ...] = ARCHIVE_ELIGIBLE_LIFECYCLE_STATUSES
    delete_source_after_archive: bool = False
    manifest_required: bool = True
    retrieval_ref_required: bool = True
    schema_version: int = EVIDENCE_ARCHIVE_SCHEMA_VERSION
    contract_id: str = EVIDENCE_ARCHIVE_POLICY_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["archive_after_lifecycle_statuses"] = list(
            self.archive_after_lifecycle_statuses
        )
        return payload


@dataclass(frozen=True, slots=True)
class EvidenceArchiveEntry:
    """One source artifact captured into an archive manifest."""

    source_path: str
    source_sha256: str
    evidence_kind: str
    size_bytes: int = 0
    lifecycle_ref: str = ""
    lifecycle_status: str = ""
    archived_path: str = ""
    retrieval_ref: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvidenceArchiveManifest:
    """Manifest proving which evidence artifacts were archived and how to recover them."""

    manifest_id: str
    policy_id: str
    archive_path: str
    source_root: str
    head_sha_at_archive: str
    entries: tuple[EvidenceArchiveEntry, ...] = ()
    created_at_utc: str = ""
    schema_version: int = EVIDENCE_ARCHIVE_SCHEMA_VERSION
    contract_id: str = EVIDENCE_ARCHIVE_MANIFEST_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["entries"] = [entry.to_dict() for entry in self.entries]
        return payload


@dataclass(frozen=True, slots=True)
class EvidenceArchiveReceipt:
    """Receipt proving an archive operation preserved evidence without deletion."""

    receipt_id: str
    policy_id: str
    manifest_id: str
    lifecycle_ref: str
    lifecycle_status: str
    archive_path: str
    manifest_path: str
    compressed: bool = True
    source_deleted: bool = False
    evidence_refs: tuple[str, ...] = ()
    created_at_utc: str = ""
    status: str = "archived"
    schema_version: int = EVIDENCE_ARCHIVE_SCHEMA_VERSION
    contract_id: str = EVIDENCE_ARCHIVE_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


def default_evidence_archive_policy(
    evidence_kind: object,
    *,
    retention_days: object = DEFAULT_EVIDENCE_RETENTION_DAYS,
    archive_root: object = DEFAULT_EVIDENCE_ARCHIVE_ROOT,
    compression: object = DEFAULT_EVIDENCE_ARCHIVE_COMPRESSION,
) -> EvidenceArchivePolicy:
    """Return the default non-deleting archive policy for one evidence family."""
    kind = coerce_string(evidence_kind) or "typed_evidence"
    days = coerce_int(retention_days) or DEFAULT_EVIDENCE_RETENTION_DAYS
    return EvidenceArchivePolicy(
        policy_id=f"evidence-archive-{kind}",
        evidence_kind=kind,
        retention_days=max(0, days),
        archive_root=coerce_string(archive_root) or DEFAULT_EVIDENCE_ARCHIVE_ROOT,
        compression=coerce_string(compression) or DEFAULT_EVIDENCE_ARCHIVE_COMPRESSION,
    )


def evidence_archive_ref(receipt_id: object) -> str:
    """Return the canonical evidence ref for an archive receipt."""
    value = coerce_string(receipt_id)
    return f"{EVIDENCE_ARCHIVE_REF_PREFIX}{value}" if value else ""


def archive_allowed_for_lifecycle_status(
    lifecycle_status: object,
    policy: EvidenceArchivePolicy | None = None,
) -> bool:
    """Return whether evidence may be archived for this lifecycle state."""
    status = coerce_string(lifecycle_status)
    active_policy = policy or default_evidence_archive_policy("typed_evidence")
    return status in active_policy.archive_after_lifecycle_statuses


def receipt_preserves_sources(receipt: EvidenceArchiveReceipt | dict[str, object]) -> bool:
    """Return true when an archive receipt proves source evidence was not deleted."""
    source_deleted = (
        receipt.source_deleted
        if isinstance(receipt, EvidenceArchiveReceipt)
        else coerce_bool(receipt.get("source_deleted"))
    )
    return not source_deleted


def evidence_archive_receipt_from_mapping(
    payload: dict[str, object],
) -> EvidenceArchiveReceipt:
    """Deserialize an archive receipt from a JSON-compatible mapping."""
    return EvidenceArchiveReceipt(
        receipt_id=coerce_string(payload.get("receipt_id")),
        policy_id=coerce_string(payload.get("policy_id")),
        manifest_id=coerce_string(payload.get("manifest_id")),
        lifecycle_ref=coerce_string(payload.get("lifecycle_ref")),
        lifecycle_status=coerce_string(payload.get("lifecycle_status")),
        archive_path=coerce_string(payload.get("archive_path")),
        manifest_path=coerce_string(payload.get("manifest_path")),
        compressed=coerce_bool(payload.get("compressed")),
        source_deleted=coerce_bool(payload.get("source_deleted")),
        evidence_refs=tuple(coerce_string_items(payload.get("evidence_refs"))),
        created_at_utc=coerce_string(payload.get("created_at_utc")),
        status=coerce_string(payload.get("status")) or "archived",
    )


__all__ = [
    "ARCHIVE_ELIGIBLE_LIFECYCLE_STATUSES",
    "DEFAULT_EVIDENCE_ARCHIVE_COMPRESSION",
    "DEFAULT_EVIDENCE_ARCHIVE_ROOT",
    "DEFAULT_EVIDENCE_RETENTION_DAYS",
    "EVIDENCE_ARCHIVE_MANIFEST_CONTRACT_ID",
    "EVIDENCE_ARCHIVE_POLICY_CONTRACT_ID",
    "EVIDENCE_ARCHIVE_RECEIPT_CONTRACT_ID",
    "EVIDENCE_ARCHIVE_REF_PREFIX",
    "EVIDENCE_ARCHIVE_SCHEMA_VERSION",
    "EvidenceArchiveEntry",
    "EvidenceArchiveManifest",
    "EvidenceArchivePolicy",
    "EvidenceArchiveReceipt",
    "archive_allowed_for_lifecycle_status",
    "default_evidence_archive_policy",
    "evidence_archive_receipt_from_mapping",
    "evidence_archive_ref",
    "receipt_preserves_sources",
]
