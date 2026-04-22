"""Orphan snapshot/source typed contract models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_mapping_items,
    coerce_string,
    coerce_string_items,
)
from .worktree_orphan_types import ORPHAN_SOURCE_KINDS, enum_value


@dataclass(frozen=True, slots=True)
class OrphanSourceClassification:
    """Policy classification attached to one orphan source."""

    state: str = "unclassified"
    known_governed_auto_sync: bool = False
    load_bearing: bool = False
    governance_owner: str = ""
    risk: str = ""
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        return payload


@dataclass(frozen=True, slots=True)
class OrphanSource:
    """One OrphanSnapshot source row discriminated by source_kind."""

    source_id: str
    source_kind: str
    source_ref: str
    path: str = ""
    repo_identity: str = ""
    branch: str = ""
    head_sha: str = ""
    dirty_path_count: int = 0
    untracked_path_count: int = 0
    unpublished_commit_shas: tuple[str, ...] = ()
    status: str = "unresolved"
    classification: OrphanSourceClassification = field(
        default_factory=OrphanSourceClassification
    )
    evidence_refs: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["unpublished_commit_shas"] = list(self.unpublished_commit_shas)
        payload["classification"] = self.classification.to_dict()
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class OrphanSnapshotStats:
    """Aggregated counts for an OrphanSnapshot."""

    total_sources: int = 0
    unresolved_sources: int = 0
    dirty_sources: int = 0
    unpublished_sources: int = 0
    prunable_sources: int = 0
    load_bearing_sources: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OrphanSnapshot:
    """AuthoritySnapshot-peer projection over orphanable work sources."""

    snapshot_id: str
    scan_at_utc: str
    scan_trigger: str
    scan_scope_applied: str
    primary_repo_identity: str
    sources: tuple[OrphanSource, ...] = ()
    stats: OrphanSnapshotStats = field(default_factory=OrphanSnapshotStats)
    load_bearing: bool = False
    snapshot_hash: str = ""
    schema_version: int = 1
    contract_id: str = "OrphanSnapshot"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["sources"] = [source.to_dict() for source in self.sources]
        payload["stats"] = self.stats.to_dict()
        return payload


def orphan_source_classification_from_mapping(
    value: object,
) -> OrphanSourceClassification:
    payload = coerce_mapping(value)
    return OrphanSourceClassification(
        state=coerce_string(payload.get("state")) or "unclassified",
        known_governed_auto_sync=coerce_bool(
            payload.get("known_governed_auto_sync")
        ),
        load_bearing=coerce_bool(payload.get("load_bearing")),
        governance_owner=coerce_string(payload.get("governance_owner")),
        risk=coerce_string(payload.get("risk")),
        notes=coerce_string_items(payload.get("notes")),
    )


def orphan_source_from_mapping(value: object) -> OrphanSource | None:
    payload = coerce_mapping(value)
    if not payload:
        return None

    required = _orphan_source_required_fields(payload)
    if required is None:
        return None

    source_id, source_ref, source_kind = required
    classification = orphan_source_classification_from_mapping(
        payload.get("classification")
    )

    return OrphanSource(
        source_id=source_id,
        source_kind=source_kind,
        source_ref=source_ref,
        path=coerce_string(payload.get("path")),
        repo_identity=coerce_string(payload.get("repo_identity")),
        branch=coerce_string(payload.get("branch")),
        head_sha=coerce_string(payload.get("head_sha")),
        dirty_path_count=coerce_int(payload.get("dirty_path_count")),
        untracked_path_count=coerce_int(payload.get("untracked_path_count")),
        unpublished_commit_shas=coerce_string_items(
            payload.get("unpublished_commit_shas")
        ),
        status=coerce_string(payload.get("status")) or "unresolved",
        classification=classification,
        evidence_refs=coerce_string_items(payload.get("evidence_refs")),
        metadata=dict(coerce_mapping(payload.get("metadata"))),
    )


def _orphan_source_required_fields(
    payload: Mapping[str, object],
) -> tuple[str, str, str] | None:
    source_id = coerce_string(payload.get("source_id"))
    source_ref = coerce_string(payload.get("source_ref"))
    source_kind = enum_value(
        coerce_string(payload.get("source_kind")),
        allowed=ORPHAN_SOURCE_KINDS,
        default="current_checkout",
    )

    if not source_id or not source_ref:
        return None

    return source_id, source_ref, source_kind


def orphan_snapshot_stats_from_mapping(value: object) -> OrphanSnapshotStats:
    payload = coerce_mapping(value)
    return OrphanSnapshotStats(
        total_sources=coerce_int(payload.get("total_sources")),
        unresolved_sources=coerce_int(payload.get("unresolved_sources")),
        dirty_sources=coerce_int(payload.get("dirty_sources")),
        unpublished_sources=coerce_int(payload.get("unpublished_sources")),
        prunable_sources=coerce_int(payload.get("prunable_sources")),
        load_bearing_sources=coerce_int(payload.get("load_bearing_sources")),
    )


def orphan_snapshot_from_mapping(value: object) -> OrphanSnapshot | None:
    payload = coerce_mapping(value)
    if not payload:
        return None

    sources = tuple(_parsed_sources(payload))

    return OrphanSnapshot(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "OrphanSnapshot",
        snapshot_id=coerce_string(payload.get("snapshot_id")),
        scan_at_utc=coerce_string(payload.get("scan_at_utc")),
        scan_trigger=coerce_string(payload.get("scan_trigger")),
        scan_scope_applied=coerce_string(payload.get("scan_scope_applied")),
        primary_repo_identity=coerce_string(payload.get("primary_repo_identity")),
        sources=sources,
        stats=orphan_snapshot_stats_from_mapping(payload.get("stats")),
        load_bearing=coerce_bool(payload.get("load_bearing")),
        snapshot_hash=coerce_string(payload.get("snapshot_hash")),
    )


def _parsed_sources(payload: Mapping[str, object]) -> tuple[OrphanSource, ...]:
    sources: list[OrphanSource] = []
    for item in coerce_mapping_items(payload.get("sources")):
        source = orphan_source_from_mapping(item)
        if source is not None:
            sources.append(source)
    return tuple(sources)


__all__ = [
    "OrphanSnapshot",
    "OrphanSnapshotStats",
    "OrphanSource",
    "OrphanSourceClassification",
    "orphan_snapshot_from_mapping",
    "orphan_source_from_mapping",
]
