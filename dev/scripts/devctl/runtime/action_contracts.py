"""Shared runtime action/run/adapter contract models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)


@dataclass(frozen=True, slots=True)
class TypedAction:
    schema_version: int
    contract_id: str
    action_id: str
    repo_pack_id: str
    parameters: dict[str, object]
    requested_by: str = ""
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class RunRecord:
    schema_version: int
    contract_id: str
    run_id: str
    action_id: str
    artifact_paths: tuple[str, ...]
    status: str = "unknown"
    findings_count: int = 0
    started_at: str = ""
    finished_at: str = ""


@dataclass(frozen=True, slots=True)
class ArtifactStore:
    schema_version: int
    contract_id: str
    root: str
    retention_policy: dict[str, object]
    managed_kinds: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProviderAdapter:
    schema_version: int
    contract_id: str
    provider_id: str
    capabilities: tuple[str, ...]
    launch_mode: str
    available: bool = True


@dataclass(frozen=True, slots=True)
class WorkflowAdapter:
    schema_version: int
    contract_id: str
    adapter_id: str
    transport: str
    allowed_actions: tuple[str, ...]
    available: bool = True


def typed_action_from_mapping(payload: Mapping[str, object]) -> TypedAction:
    parameters = dict(coerce_mapping(payload.get("parameters")))
    return TypedAction(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "TypedAction",
        action_id=coerce_string(payload.get("action_id")),
        repo_pack_id=coerce_string(payload.get("repo_pack_id")),
        parameters=parameters,
        requested_by=coerce_string(payload.get("requested_by")),
        dry_run=coerce_bool(payload.get("dry_run")),
    )


def run_record_from_mapping(payload: Mapping[str, object]) -> RunRecord:
    return RunRecord(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "RunRecord",
        run_id=coerce_string(payload.get("run_id")),
        action_id=coerce_string(payload.get("action_id")),
        artifact_paths=coerce_string_items(payload.get("artifact_paths")),
        status=coerce_string(payload.get("status")) or "unknown",
        findings_count=coerce_int(payload.get("findings_count")),
        started_at=coerce_string(payload.get("started_at")),
        finished_at=coerce_string(payload.get("finished_at")),
    )


def provider_adapter_from_mapping(payload: Mapping[str, object]) -> ProviderAdapter:
    return ProviderAdapter(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "ProviderAdapter",
        provider_id=coerce_string(payload.get("provider_id")),
        capabilities=coerce_string_items(payload.get("capabilities")),
        launch_mode=coerce_string(payload.get("launch_mode")),
        available=coerce_bool(payload.get("available", True)),
    )


def workflow_adapter_from_mapping(payload: Mapping[str, object]) -> WorkflowAdapter:
    return WorkflowAdapter(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "WorkflowAdapter",
        adapter_id=coerce_string(payload.get("adapter_id")),
        transport=coerce_string(payload.get("transport")),
        allowed_actions=coerce_string_items(payload.get("allowed_actions")),
        available=coerce_bool(payload.get("available", True)),
    )
