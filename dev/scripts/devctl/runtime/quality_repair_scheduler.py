"""File-hash applicability for cloud quality findings."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .file_hashes import existing_file_hashes


@dataclass(frozen=True, slots=True)
class FindingAffectedScope:
    path: str
    file_sha256: str
    contract_id: str = "FindingAffectedScope"
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class CloudFinding:
    finding_id: str
    source_snapshot_id: str
    affected_scopes: tuple[FindingAffectedScope, ...]
    summary: str = ""
    severity: str = ""
    source_ref: str = ""
    contract_id: str = "CloudFinding"
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class FindingApplicability:
    finding_id: str
    status: str
    repair_authorized: bool
    current_paths: tuple[str, ...] = ()
    stale_paths: tuple[str, ...] = ()
    missing_paths: tuple[str, ...] = ()
    observed_hashes: dict[str, str] | None = None
    reason: str = ""
    contract_id: str = "FindingApplicability"
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class RepairPacket:
    repair_packet_id: str
    finding_id: str
    affected_paths: tuple[str, ...]
    source_snapshot_id: str
    reason: str
    contract_id: str = "RepairPacket"
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class StaleFindingReceipt:
    receipt_id: str
    finding_id: str
    stale_paths: tuple[str, ...]
    missing_paths: tuple[str, ...]
    observed_hashes: dict[str, str] | None
    reason: str
    contract_id: str = "StaleFindingReceipt"
    schema_version: int = 1


def reconcile_finding_applicability(
    *,
    repo_root: Path,
    finding: CloudFinding,
) -> FindingApplicability:
    """Authorize repair only when every affected file still matches by hash."""
    expected = {
        scope.path: scope.file_sha256
        for scope in finding.affected_scopes
        if scope.path and scope.file_sha256
    }
    observed = existing_file_hashes(repo_root, tuple(expected))
    missing = tuple(path for path in expected if path not in observed)
    stale = tuple(
        path for path, expected_hash in expected.items()
        if path in observed and observed[path] != expected_hash
    )
    current = tuple(
        path for path, expected_hash in expected.items()
        if observed.get(path) == expected_hash
    )
    if not expected:
        status = "reconciliation_only"
        reason = "no_affected_file_hashes"
    elif missing:
        status = "missing_file"
        reason = "affected_file_missing"
    elif stale:
        status = "stale"
        reason = "affected_file_hash_changed"
    else:
        status = "current"
        reason = "all_affected_file_hashes_match"
    return FindingApplicability(
        finding_id=finding.finding_id,
        status=status,
        repair_authorized=status == "current",
        current_paths=current,
        stale_paths=stale,
        missing_paths=missing,
        observed_hashes=observed,
        reason=reason,
    )


def repair_packet_for_applicable_finding(
    *,
    finding: CloudFinding,
    applicability: FindingApplicability,
) -> RepairPacket | None:
    if not applicability.repair_authorized:
        return None
    return RepairPacket(
        repair_packet_id=_stable_id("repair", finding.finding_id),
        finding_id=finding.finding_id,
        affected_paths=applicability.current_paths,
        source_snapshot_id=finding.source_snapshot_id,
        reason=applicability.reason,
    )


def stale_receipt_for_inapplicable_finding(
    *,
    finding: CloudFinding,
    applicability: FindingApplicability,
) -> StaleFindingReceipt | None:
    if applicability.repair_authorized:
        return None
    return StaleFindingReceipt(
        receipt_id=_stable_id("stale", finding.finding_id, applicability.status),
        finding_id=finding.finding_id,
        stale_paths=applicability.stale_paths,
        missing_paths=applicability.missing_paths,
        observed_hashes=applicability.observed_hashes,
        reason=applicability.reason,
    )


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


__all__ = [
    "CloudFinding",
    "FindingAffectedScope",
    "FindingApplicability",
    "RepairPacket",
    "StaleFindingReceipt",
    "reconcile_finding_applicability",
    "repair_packet_for_applicable_finding",
    "stale_receipt_for_inapplicable_finding",
]
