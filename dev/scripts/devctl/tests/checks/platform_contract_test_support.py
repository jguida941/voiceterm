"""Shared helpers for platform-contract guard tests."""

from __future__ import annotations

from dataclasses import replace

from dev.scripts.devctl.platform.blueprint import build_platform_blueprint


def drop_contract_field(contract_id: str, field_name: str):
    """Return a blueprint with one required contract field removed."""
    blueprint = build_platform_blueprint()
    shared_contracts = []
    for contract in blueprint.shared_contracts:
        if contract.contract_id != contract_id:
            shared_contracts.append(contract)
            continue
        shared_contracts.append(
            replace(
                contract,
                required_fields=tuple(
                    field for field in contract.required_fields if field.name != field_name
                ),
            )
        )
    return replace(blueprint, shared_contracts=tuple(shared_contracts))


def rewrite_artifact_schema(contract_id: str, *, schema_version: int):
    """Return a blueprint with one artifact schema row rewritten."""
    blueprint = build_platform_blueprint()
    artifact_schemas = []
    for spec in blueprint.artifact_schemas:
        if spec.contract_id != contract_id:
            artifact_schemas.append(spec)
            continue
        artifact_schemas.append(replace(spec, schema_version=schema_version))
    return replace(blueprint, artifact_schemas=tuple(artifact_schemas))
