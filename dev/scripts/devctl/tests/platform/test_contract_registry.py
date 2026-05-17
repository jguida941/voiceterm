"""Tests for the repo-owned platform contract registry."""

from __future__ import annotations

from dev.scripts.devctl.platform.blueprint import build_platform_blueprint
from dev.scripts.devctl.platform.contract_registry import (
    build_contract_registry_rows,
    read_contract_registry_rows,
    write_contract_registry_rows,
)


def test_build_contract_registry_rows_covers_blueprint_contracts_and_artifacts() -> None:
    blueprint = build_platform_blueprint()

    rows = build_contract_registry_rows(blueprint)

    assert len(rows) <= len(blueprint.shared_contracts) + len(blueprint.artifact_schemas)
    assert len(
        {
            (row.registered_contract_id, row.registered_schema_version, row.python_owner_path)
            for row in rows
        }
    ) == len(rows)
    assert any(
        row.entry_kind == "shared_contract"
        and row.registered_contract_id == "PlatformContractRegistryRow"
        for row in rows
    )
    assert any(
        row.entry_kind == "artifact_schema"
        and row.registered_contract_id == "PlatformContractRegistry"
        for row in rows
    )
    assert any(
        row.entry_kind == "artifact_schema"
        and row.registered_contract_id == "DogfoodSelfCheckReceipt"
        for row in rows
    )
    assert any(
        row.entry_kind == "artifact_schema"
        and row.registered_contract_id == "ReviewerAuditReceipt"
        for row in rows
    )
    assert any(
        row.entry_kind == "artifact_schema"
        and row.registered_contract_id == "SessionActivityLog"
        for row in rows
    )
    assert any(
        row.entry_kind == "shared_contract"
        and row.registered_contract_id == "DurableSchemaPolicy"
        for row in rows
    )
    assert any(
        row.entry_kind == "shared_contract"
        and row.registered_contract_id == "SchemaMigrationSpine"
        for row in rows
    )
    assert any(
        row.entry_kind == "shared_contract"
        and row.registered_contract_id == "SystemMapSnapshot"
        for row in rows
    )


def test_contract_registry_rows_round_trip_through_jsonl(tmp_path) -> None:
    path = tmp_path / "contract_registry.jsonl"
    rows = build_contract_registry_rows()

    write_contract_registry_rows(path, rows)
    stored = read_contract_registry_rows(path)

    assert stored == rows
