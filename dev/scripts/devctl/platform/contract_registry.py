"""Helpers for the repo-owned shared platform contract registry."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from importlib import import_module
from pathlib import Path

from ..runtime.state_store_authority import (
    StateStoreWriteResult,
    read_json_mappings_strict,
    replace_json_mappings,
)
from .blueprint import build_platform_blueprint
from .contract_registry_models import (
    CONTRACT_REGISTRY_STORE_REL,
    ContractRegistryRow,
    DEFAULT_CONTRACT_REGISTRY_PARITY_COMMAND,
)
from .contracts import ContractSpec, PlatformBlueprint

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PLATFORM_ROOT = _REPO_ROOT / "dev/scripts/devctl/platform"


def build_contract_registry_rows(
    blueprint: PlatformBlueprint | None = None,
) -> tuple[ContractRegistryRow, ...]:
    """Return the canonical repo-owned registry rows for the current blueprint."""
    blueprint = blueprint or build_platform_blueprint()
    rows: list[ContractRegistryRow] = []
    for contract in blueprint.shared_contracts:
        schema_version = _runtime_schema_version(contract)
        rows.append(
            ContractRegistryRow(
                registered_contract_id=contract.contract_id,
                entry_kind=contract.registry_entry_kind,
                python_owner_path=_runtime_owner_path(contract),
                rust_owner_path="",
                fixture_path=_fixture_path(contract.contract_id, schema_version),
                registered_schema_version=schema_version,
                ownership_mode=contract.registry_ownership_mode,
                parity_command=DEFAULT_CONTRACT_REGISTRY_PARITY_COMMAND,
            )
        )
    for spec in blueprint.artifact_schemas:
        rows.append(
            ContractRegistryRow(
                registered_contract_id=spec.contract_id,
                entry_kind="artifact_schema",
                python_owner_path=spec.emitter_path,
                rust_owner_path="",
                fixture_path=_fixture_path(spec.contract_id, spec.schema_version),
                registered_schema_version=spec.schema_version,
                ownership_mode="python_only",
                parity_command=DEFAULT_CONTRACT_REGISTRY_PARITY_COMMAND,
            )
        )
    return _dedupe_same_owner_rows(tuple(sorted(rows, key=lambda row: row.key())))


def _dedupe_same_owner_rows(
    rows: tuple[ContractRegistryRow, ...],
) -> tuple[ContractRegistryRow, ...]:
    """Collapse duplicate registrations when they point at one owner path.

    Runtime contracts can also be artifact schemas. When both rows use the same
    contract id, schema version, and owner path, the registry keeps the artifact
    row as the canonical external artifact surface and lets the blueprint retain
    the runtime dataclass contract for closure checks.
    """
    buckets: dict[tuple[str, int], list[ContractRegistryRow]] = {}
    for row in rows:
        buckets.setdefault(
            (row.registered_contract_id, row.registered_schema_version),
            [],
        ).append(row)

    deduped: list[ContractRegistryRow] = []
    for grouped in buckets.values():
        owner_keys = {
            (row.python_owner_path, row.rust_owner_path)
            for row in grouped
        }
        if len(grouped) > 1 and len(owner_keys) == 1:
            artifact_rows = [
                row for row in grouped if row.entry_kind == "artifact_schema"
            ]
            deduped.append(artifact_rows[0] if artifact_rows else grouped[0])
            continue
        deduped.extend(grouped)
    return tuple(sorted(deduped, key=lambda row: row.key()))


def read_contract_registry_rows(path: Path) -> tuple[ContractRegistryRow, ...]:
    """Read typed registry rows from the repo-owned JSONL store."""
    return tuple(
        ContractRegistryRow.from_mapping(payload)
        for payload in read_json_mappings_strict(path)
    )


def write_contract_registry_rows(
    path: Path,
    rows: tuple[ContractRegistryRow, ...],
) -> StateStoreWriteResult:
    """Atomically replace the repo-owned contract registry store."""
    return replace_json_mappings(
        path,
        tuple(row.to_dict() for row in rows),
        store_id="platform_contract_registry",
    )


def contract_registry_path(repo_root: Path) -> Path:
    """Return the canonical registry path for one repo."""
    return repo_root / CONTRACT_REGISTRY_STORE_REL


def _runtime_owner_path(contract: ContractSpec) -> str:
    if not contract.runtime_model:
        return _platform_contract_owner_path(contract.contract_id)
    module_name = contract.runtime_model.partition(":")[0]
    return module_name.replace(".", "/") + ".py"


def _runtime_schema_version(contract: ContractSpec) -> int:
    if not contract.runtime_model:
        return 1
    runtime_type = _import_symbol(contract.runtime_model)
    if not is_dataclass(runtime_type):
        return 1
    for field in fields(runtime_type):
        if field.name != "schema_version":
            continue
        default = field.default
        if isinstance(default, int):
            return default
        break
    return 1


def _import_symbol(target: str) -> object:
    module_name, _, attr_name = target.partition(":")
    if not module_name or not attr_name:
        raise ValueError(f"Invalid import target `{target}`.")
    module = import_module(module_name)
    return getattr(module, attr_name)


def _fixture_path(contract_id: str, schema_version: int) -> str:
    return f"dev/test_data/schema_fixtures/{contract_id}/{schema_version}"


def _platform_contract_owner_path(contract_id: str) -> str:
    tokens = (f'contract_id="{contract_id}"', f"contract_id='{contract_id}'")
    for path in sorted(_PLATFORM_ROOT.rglob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if not any(token in text for token in tokens):
            continue
        return path.relative_to(_REPO_ROOT).as_posix()
    return ""


__all__ = [
    "CONTRACT_REGISTRY_STORE_REL",
    "build_contract_registry_rows",
    "contract_registry_path",
    "read_contract_registry_rows",
    "write_contract_registry_rows",
]
