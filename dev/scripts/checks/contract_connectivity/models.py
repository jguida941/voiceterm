"""Typed report models for contract-connectivity analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LayerContractCount:
    """Dataclass inventory count for one architecture layer."""

    layer: str
    contract_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OrphanedContractFinding:
    """A dataclass contract with no importers outside its own module."""

    contract_name: str
    layer: str
    module_name: str
    module_path: str
    field_names: tuple[str, ...]
    importer_modules: tuple[str, ...] = ()
    importer_paths: tuple[str, ...] = ()
    cross_layer_importer_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["field_names"] = list(self.field_names)
        payload["importer_modules"] = list(self.importer_modules)
        payload["importer_paths"] = list(self.importer_paths)
        return payload


@dataclass(frozen=True, slots=True)
class DuplicateContractFinding:
    """Two dataclasses whose field sets overlap enough to indicate duplication."""

    left_contract_name: str
    left_layer: str
    left_module_name: str
    left_module_path: str
    right_contract_name: str
    right_layer: str
    right_module_name: str
    right_module_path: str
    overlap_ratio: float
    shared_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["shared_fields"] = list(self.shared_fields)
        return payload


@dataclass(frozen=True, slots=True)
class StrandedContractFinding:
    """A module rebuilding typed contract state from raw mapping keys."""

    consumer_module_name: str
    consumer_path: str
    contract_name: str
    contract_layer: str
    contract_module_name: str
    contract_module_path: str
    overlap_ratio: float
    shared_raw_keys: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["shared_raw_keys"] = list(self.shared_raw_keys)
        return payload


@dataclass(frozen=True, slots=True)
class ContractConnectivityReport:
    """Typed report emitted by ``check_contract_connectivity.py``."""

    schema_version: int = 1
    contract_id: str = "ContractConnectivityReport"
    command: str = "check_contract_connectivity"
    mode: str = "working-tree"
    since_ref: str = ""
    head_ref: str = "HEAD"
    ok: bool = True
    contracts_scanned: int = 0
    importer_modules_scanned: int = 0
    layer_counts: tuple[LayerContractCount, ...] = ()
    orphaned_contracts: tuple[OrphanedContractFinding, ...] = ()
    duplicate_contracts: tuple[DuplicateContractFinding, ...] = ()
    stranded_consumers: tuple[StrandedContractFinding, ...] = ()
    new_orphaned_contracts: tuple[OrphanedContractFinding, ...] = ()
    new_duplicate_contracts: tuple[DuplicateContractFinding, ...] = ()
    new_stranded_consumers: tuple[StrandedContractFinding, ...] = ()
    baseline_orphaned_count: int = 0
    baseline_duplicate_count: int = 0
    baseline_stranded_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["layer_counts"] = [item.to_dict() for item in self.layer_counts]
        payload["orphaned_contracts"] = [
            item.to_dict() for item in self.orphaned_contracts
        ]
        payload["duplicate_contracts"] = [
            item.to_dict() for item in self.duplicate_contracts
        ]
        payload["stranded_consumers"] = [
            item.to_dict() for item in self.stranded_consumers
        ]
        payload["new_orphaned_contracts"] = [
            item.to_dict() for item in self.new_orphaned_contracts
        ]
        payload["new_duplicate_contracts"] = [
            item.to_dict() for item in self.new_duplicate_contracts
        ]
        payload["new_stranded_consumers"] = [
            item.to_dict() for item in self.new_stranded_consumers
        ]
        return payload
