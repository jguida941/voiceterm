"""Typed baseline inventory receipt for governed authority surfaces."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .plan_ingestion_phase0_models import RepoStateFingerprint
from .state_store_authority import append_json_mapping
from .value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_mapping_items,
    coerce_string,
    coerce_string_items,
)

BASELINE_AUTHORITY_INVENTORY_CONTRACT_ID = "BaselineAuthorityInventoryReceipt"
BASELINE_AUTHORITY_INVENTORY_SCHEMA_VERSION = 1
DEFAULT_BASELINE_AUTHORITY_INVENTORY_REL = Path(
    "dev/state/baseline_authority_inventories.jsonl"
)


@dataclass(frozen=True, slots=True)
class InventoryCodeSite:
    """One code location discovered by the baseline inventory scan."""

    path: str
    symbol: str = ""
    line_number: int = 0
    pattern: str = ""
    category: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object] | object) -> "InventoryCodeSite":
        mapping = coerce_mapping(payload)
        return cls(
            path=coerce_string(mapping.get("path")),
            symbol=coerce_string(mapping.get("symbol")),
            line_number=coerce_int(mapping.get("line_number")),
            pattern=coerce_string(mapping.get("pattern")),
            category=coerce_string(mapping.get("category")),
        )


@dataclass(frozen=True, slots=True)
class AuthorityStoreEntry:
    """One governed store and the current writer policy around it."""

    path: str
    store_kind: str
    writer_ref: str
    locking_policy: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object] | object,
    ) -> "AuthorityStoreEntry":
        mapping = coerce_mapping(payload)
        return cls(
            path=coerce_string(mapping.get("path")),
            store_kind=coerce_string(mapping.get("store_kind")),
            writer_ref=coerce_string(mapping.get("writer_ref")),
            locking_policy=coerce_string(mapping.get("locking_policy")),
        )


@dataclass(frozen=True, slots=True)
class DuplicateSystemCluster:
    """One known duplicate-system cluster that baseline work must collapse."""

    cluster_id: str
    summary: str
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object] | object,
    ) -> "DuplicateSystemCluster":
        mapping = coerce_mapping(payload)
        return cls(
            cluster_id=coerce_string(mapping.get("cluster_id")),
            summary=coerce_string(mapping.get("summary")),
            evidence_refs=coerce_string_items(mapping.get("evidence_refs")),
        )


@dataclass(frozen=True, slots=True)
class BaselineAuthorityInventoryReceipt:
    """Typed receipt capturing the current authority substrate before mutation."""

    inventory_id: str
    recorded_at_utc: str
    repo_root: str
    repo_state_fingerprint: RepoStateFingerprint
    search_patterns: tuple[str, ...] = ()
    file_counts: dict[str, int] | None = None
    state_store_entries: tuple[AuthorityStoreEntry, ...] = ()
    state_files: tuple[str, ...] = ()
    direct_write_sites: tuple[InventoryCodeSite, ...] = ()
    direct_read_sites: tuple[InventoryCodeSite, ...] = ()
    generated_projection_paths: tuple[str, ...] = ()
    workflow_surfaces: tuple[str, ...] = ()
    check_surfaces: tuple[str, ...] = ()
    bundle_surfaces: tuple[str, ...] = ()
    packet_kinds: tuple[str, ...] = ()
    reducer_sites: tuple[InventoryCodeSite, ...] = ()
    event_producer_sites: tuple[InventoryCodeSite, ...] = ()
    event_subscriber_sites: tuple[InventoryCodeSite, ...] = ()
    compatibility_shims: tuple[InventoryCodeSite, ...] = ()
    duplicate_system_clusters: tuple[DuplicateSystemCluster, ...] = ()
    system_catalog_counts: dict[str, int] | None = None
    connectivity_registry_counts: dict[str, int] | None = None
    receipt_path: str = ""
    status: str = "accepted"
    dry_run: bool = False
    schema_version: int = BASELINE_AUTHORITY_INVENTORY_SCHEMA_VERSION
    contract_id: str = BASELINE_AUTHORITY_INVENTORY_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["repo_state_fingerprint"] = self.repo_state_fingerprint.to_dict()
        payload["search_patterns"] = list(self.search_patterns)
        payload["state_store_entries"] = [
            item.to_dict() for item in self.state_store_entries
        ]
        payload["state_files"] = list(self.state_files)
        payload["direct_write_sites"] = [
            item.to_dict() for item in self.direct_write_sites
        ]
        payload["direct_read_sites"] = [item.to_dict() for item in self.direct_read_sites]
        payload["generated_projection_paths"] = list(self.generated_projection_paths)
        payload["workflow_surfaces"] = list(self.workflow_surfaces)
        payload["check_surfaces"] = list(self.check_surfaces)
        payload["bundle_surfaces"] = list(self.bundle_surfaces)
        payload["packet_kinds"] = list(self.packet_kinds)
        payload["reducer_sites"] = [item.to_dict() for item in self.reducer_sites]
        payload["event_producer_sites"] = [
            item.to_dict() for item in self.event_producer_sites
        ]
        payload["event_subscriber_sites"] = [
            item.to_dict() for item in self.event_subscriber_sites
        ]
        payload["compatibility_shims"] = [
            item.to_dict() for item in self.compatibility_shims
        ]
        payload["duplicate_system_clusters"] = [
            item.to_dict() for item in self.duplicate_system_clusters
        ]
        payload["file_counts"] = dict(self.file_counts or {})
        payload["system_catalog_counts"] = dict(self.system_catalog_counts or {})
        payload["connectivity_registry_counts"] = dict(
            self.connectivity_registry_counts or {}
        )
        return payload

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object] | object,
    ) -> "BaselineAuthorityInventoryReceipt":
        mapping = coerce_mapping(payload)
        return cls(
            inventory_id=coerce_string(mapping.get("inventory_id")),
            recorded_at_utc=coerce_string(mapping.get("recorded_at_utc")),
            repo_root=coerce_string(mapping.get("repo_root")),
            repo_state_fingerprint=RepoStateFingerprint.from_mapping(
                mapping.get("repo_state_fingerprint")
            ),
            search_patterns=coerce_string_items(mapping.get("search_patterns")),
            file_counts={
                str(key): coerce_int(value)
                for key, value in coerce_mapping(mapping.get("file_counts")).items()
            },
            state_store_entries=tuple(
                AuthorityStoreEntry.from_mapping(item)
                for item in coerce_mapping_items(mapping.get("state_store_entries"))
            ),
            state_files=coerce_string_items(mapping.get("state_files")),
            direct_write_sites=tuple(
                InventoryCodeSite.from_mapping(item)
                for item in coerce_mapping_items(mapping.get("direct_write_sites"))
            ),
            direct_read_sites=tuple(
                InventoryCodeSite.from_mapping(item)
                for item in coerce_mapping_items(mapping.get("direct_read_sites"))
            ),
            generated_projection_paths=coerce_string_items(
                mapping.get("generated_projection_paths")
            ),
            workflow_surfaces=coerce_string_items(mapping.get("workflow_surfaces")),
            check_surfaces=coerce_string_items(mapping.get("check_surfaces")),
            bundle_surfaces=coerce_string_items(mapping.get("bundle_surfaces")),
            packet_kinds=coerce_string_items(mapping.get("packet_kinds")),
            reducer_sites=tuple(
                InventoryCodeSite.from_mapping(item)
                for item in coerce_mapping_items(mapping.get("reducer_sites"))
            ),
            event_producer_sites=tuple(
                InventoryCodeSite.from_mapping(item)
                for item in coerce_mapping_items(mapping.get("event_producer_sites"))
            ),
            event_subscriber_sites=tuple(
                InventoryCodeSite.from_mapping(item)
                for item in coerce_mapping_items(mapping.get("event_subscriber_sites"))
            ),
            compatibility_shims=tuple(
                InventoryCodeSite.from_mapping(item)
                for item in coerce_mapping_items(mapping.get("compatibility_shims"))
            ),
            duplicate_system_clusters=tuple(
                DuplicateSystemCluster.from_mapping(item)
                for item in coerce_mapping_items(
                    mapping.get("duplicate_system_clusters")
                )
            ),
            system_catalog_counts={
                str(key): coerce_int(value)
                for key, value in coerce_mapping(
                    mapping.get("system_catalog_counts")
                ).items()
            },
            connectivity_registry_counts={
                str(key): coerce_int(value)
                for key, value in coerce_mapping(
                    mapping.get("connectivity_registry_counts")
                ).items()
            },
            receipt_path=coerce_string(mapping.get("receipt_path")),
            status=coerce_string(mapping.get("status")) or "accepted",
            dry_run=bool(mapping.get("dry_run")),
            schema_version=coerce_int(mapping.get("schema_version"))
            or BASELINE_AUTHORITY_INVENTORY_SCHEMA_VERSION,
            contract_id=coerce_string(mapping.get("contract_id"))
            or BASELINE_AUTHORITY_INVENTORY_CONTRACT_ID,
        )


def baseline_authority_inventory_id(
    receipt: BaselineAuthorityInventoryReceipt,
) -> str:
    """Return a stable hash for the receipt payload excluding storage location."""
    payload = receipt.to_dict()
    payload["inventory_id"] = ""
    payload["receipt_path"] = ""
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return f"sha256:{digest.hexdigest()}"


def append_baseline_authority_inventory_receipt(
    receipt: BaselineAuthorityInventoryReceipt,
    *,
    repo_root: Path,
    receipt_path: str | Path | None = None,
) -> Path:
    """Append one baseline inventory receipt with a locked write."""
    path = _receipt_path(repo_root, receipt_path)
    stored = replace(receipt, receipt_path=str(path.resolve()))
    if not stored.inventory_id:
        stored = replace(
            stored,
            inventory_id=baseline_authority_inventory_id(stored),
        )
    append_json_mapping(
        path,
        stored.to_dict(),
        store_id="baseline_authority_inventories",
    )
    return path


def read_baseline_authority_inventory_receipts(
    path: Path,
) -> tuple[BaselineAuthorityInventoryReceipt, ...]:
    """Read baseline inventory receipts from the append-only ledger."""
    if not path.exists():
        return ()
    rows: list[BaselineAuthorityInventoryReceipt] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        rows.append(BaselineAuthorityInventoryReceipt.from_mapping(payload))
    return tuple(rows)


def _receipt_path(repo_root: Path, receipt_path: str | Path | None) -> Path:
    path = Path(receipt_path) if receipt_path else DEFAULT_BASELINE_AUTHORITY_INVENTORY_REL
    if path.is_absolute():
        return path
    return repo_root / path


__all__ = [
    "AuthorityStoreEntry",
    "BASELINE_AUTHORITY_INVENTORY_CONTRACT_ID",
    "BASELINE_AUTHORITY_INVENTORY_SCHEMA_VERSION",
    "BaselineAuthorityInventoryReceipt",
    "DEFAULT_BASELINE_AUTHORITY_INVENTORY_REL",
    "DuplicateSystemCluster",
    "InventoryCodeSite",
    "append_baseline_authority_inventory_receipt",
    "baseline_authority_inventory_id",
    "read_baseline_authority_inventory_receipts",
]
