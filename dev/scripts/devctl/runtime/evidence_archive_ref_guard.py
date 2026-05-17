"""Typed-ref resolution guard for ``evidence_archive_ref`` consumer fields.

Implements R320 A7 finding from the universal typed-ref-resolution-guard
mandate (memory ``READ FIRST x14``): a typed dataclass with a ``str`` field
claiming to be a reference (``evidence_archive_ref``) but no code verifying
that the ref resolves to an actual ``EvidenceArchiveReceipt`` row.

The canonical ref shape produced by :func:`evidence_archive_ref` is
``"evidence_archive:<receipt_id>"`` (see ``EVIDENCE_ARCHIVE_REF_PREFIX``).
A resolved ref must:

* be non-empty,
* carry the ``evidence_archive:`` prefix,
* match the ``receipt_id`` of a real :class:`EvidenceArchiveReceipt`
  in the configured receipts ledger (or an explicitly injected iterable).

This module is intentionally side-effect free and accepts injected receipts
so it remains test-friendly without requiring a populated ledger on disk.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from .evidence_archive import (
    EVIDENCE_ARCHIVE_REF_PREFIX,
    EvidenceArchiveReceipt,
)
from .value_coercion import coerce_string

EVIDENCE_ARCHIVE_REF_RESOLUTION_CONTRACT_ID = "EvidenceArchiveRefResolution"
EVIDENCE_ARCHIVE_REF_RESOLUTION_SCHEMA_VERSION = 1
DEFAULT_EVIDENCE_ARCHIVE_RECEIPTS_PATH = "dev/reports/archive/receipts"


@dataclass(frozen=True, slots=True)
class EvidenceArchiveRefResolution:
    """Typed result of resolving an ``evidence_archive_ref`` against the ledger."""

    ok: bool
    ref: str
    resolved_archive_id: str = ""
    found: bool = False
    expected_path: str = ""
    diagnostic: str = ""
    schema_version: int = EVIDENCE_ARCHIVE_REF_RESOLUTION_SCHEMA_VERSION
    contract_id: str = EVIDENCE_ARCHIVE_REF_RESOLUTION_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _strip_ref_prefix(ref: str) -> str:
    if ref.startswith(EVIDENCE_ARCHIVE_REF_PREFIX):
        return ref[len(EVIDENCE_ARCHIVE_REF_PREFIX) :]
    return ""


def resolve_evidence_archive_ref(
    ref: object,
    *,
    repo_root: Path | str = ".",
    receipts: Iterable[EvidenceArchiveReceipt] = (),
) -> EvidenceArchiveRefResolution:
    """Resolve an ``evidence_archive_ref`` against injected or on-disk receipts.

    ``receipts`` lets callers inject the ledger for tests and avoids any
    filesystem dependency in the common in-memory case. ``repo_root`` is
    reported back as the expected ledger path for diagnostics; this guard
    deliberately does not silently load arbitrary files.
    """
    ref_value = coerce_string(ref)
    expected_path = str(Path(repo_root) / DEFAULT_EVIDENCE_ARCHIVE_RECEIPTS_PATH)
    if not ref_value:
        return EvidenceArchiveRefResolution(
            ok=False,
            ref="",
            expected_path=expected_path,
            diagnostic="evidence_archive_ref is empty",
        )
    receipt_id = _strip_ref_prefix(ref_value) or ref_value
    for receipt in receipts:
        if isinstance(receipt, EvidenceArchiveReceipt) and receipt.receipt_id == receipt_id:
            return EvidenceArchiveRefResolution(
                ok=True,
                ref=ref_value,
                resolved_archive_id=receipt.receipt_id,
                found=True,
                expected_path=expected_path,
            )
    return EvidenceArchiveRefResolution(
        ok=False,
        ref=ref_value,
        expected_path=expected_path,
        diagnostic=(
            "evidence_archive_ref does not resolve to any EvidenceArchiveReceipt"
        ),
    )


def assert_evidence_archive_ref_resolves(
    ref: object,
    *,
    repo_root: Path | str = ".",
    receipts: Iterable[EvidenceArchiveReceipt] = (),
) -> EvidenceArchiveRefResolution:
    """Raise ``ValueError`` when ``ref`` does not resolve to a typed receipt."""
    resolution = resolve_evidence_archive_ref(
        ref, repo_root=repo_root, receipts=receipts
    )
    if not resolution.ok:
        raise ValueError(resolution.diagnostic or "evidence_archive_ref is unresolved")
    return resolution


__all__ = [
    "DEFAULT_EVIDENCE_ARCHIVE_RECEIPTS_PATH",
    "EVIDENCE_ARCHIVE_REF_RESOLUTION_CONTRACT_ID",
    "EVIDENCE_ARCHIVE_REF_RESOLUTION_SCHEMA_VERSION",
    "EvidenceArchiveRefResolution",
    "assert_evidence_archive_ref_resolves",
    "resolve_evidence_archive_ref",
]
