"""Typed models for the shared platform contract registry."""

from __future__ import annotations

from dataclasses import dataclass

from ..runtime.value_coercion import coerce_int, coerce_string

CONTRACT_REGISTRY_CONTRACT_ID = "PlatformContractRegistry"
CONTRACT_REGISTRY_ROW_CONTRACT_ID = "PlatformContractRegistryRow"
CONTRACT_REGISTRY_SCHEMA_VERSION = 1
CONTRACT_REGISTRY_STORE_REL = "dev/state/contract_registry.jsonl"
DEFAULT_CONTRACT_REGISTRY_PARITY_COMMAND = (
    "python3 dev/scripts/checks/check_platform_contract_closure.py --format json"
)
CONTRACT_REGISTRY_ENTRY_KINDS = frozenset(
    {"artifact_schema", "authority_composition", "shared_contract"}
)
CONTRACT_REGISTRY_OWNERSHIP_MODES = frozenset(
    {"python_only", "rust_only", "shared", "rust_primary", "system"}
)


@dataclass(frozen=True, slots=True)
class ContractRegistryRow:
    """One repo-owned registry row describing a portable contract family."""

    registered_contract_id: str
    entry_kind: str
    python_owner_path: str
    rust_owner_path: str = ""
    fixture_path: str = ""
    registered_schema_version: int = 1
    ownership_mode: str = "python_only"
    parity_command: str = DEFAULT_CONTRACT_REGISTRY_PARITY_COMMAND
    registry_path: str = CONTRACT_REGISTRY_STORE_REL
    schema_version: int = CONTRACT_REGISTRY_SCHEMA_VERSION
    contract_id: str = CONTRACT_REGISTRY_ROW_CONTRACT_ID

    def key(self) -> tuple[str, str]:
        return self.entry_kind, self.registered_contract_id

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_id": self.registered_contract_id,
            "entry_kind": self.entry_kind,
            "python_owner_path": self.python_owner_path,
            "rust_owner_path": self.rust_owner_path,
            "fixture_path": self.fixture_path,
            "schema_version": self.registered_schema_version,
            "ownership_mode": self.ownership_mode,
            "parity_command": self.parity_command,
            "registry_path": self.registry_path,
            "registry_row_contract_id": self.contract_id,
            "registry_row_schema_version": self.schema_version,
        }

    @classmethod
    def from_mapping(cls, payload: object) -> "ContractRegistryRow":
        if not isinstance(payload, dict):
            raise TypeError(f"expected mapping payload, got {type(payload)!r}")
        return cls(
            registered_contract_id=coerce_string(payload.get("contract_id")),
            entry_kind=coerce_string(payload.get("entry_kind")),
            python_owner_path=coerce_string(payload.get("python_owner_path")),
            rust_owner_path=coerce_string(payload.get("rust_owner_path")),
            fixture_path=coerce_string(payload.get("fixture_path")),
            registered_schema_version=coerce_int(payload.get("schema_version")) or 1,
            ownership_mode=coerce_string(payload.get("ownership_mode"))
            or "python_only",
            parity_command=coerce_string(payload.get("parity_command"))
            or DEFAULT_CONTRACT_REGISTRY_PARITY_COMMAND,
            registry_path=coerce_string(payload.get("registry_path"))
            or CONTRACT_REGISTRY_STORE_REL,
            schema_version=coerce_int(payload.get("registry_row_schema_version"))
            or CONTRACT_REGISTRY_SCHEMA_VERSION,
            contract_id=coerce_string(payload.get("registry_row_contract_id"))
            or CONTRACT_REGISTRY_ROW_CONTRACT_ID,
        )


__all__ = [
    "CONTRACT_REGISTRY_CONTRACT_ID",
    "CONTRACT_REGISTRY_ENTRY_KINDS",
    "CONTRACT_REGISTRY_OWNERSHIP_MODES",
    "CONTRACT_REGISTRY_ROW_CONTRACT_ID",
    "CONTRACT_REGISTRY_SCHEMA_VERSION",
    "CONTRACT_REGISTRY_STORE_REL",
    "ContractRegistryRow",
    "DEFAULT_CONTRACT_REGISTRY_PARITY_COMMAND",
]
