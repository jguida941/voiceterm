"""Shared helpers for platform contract-closure enforcement."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from importlib import import_module

from dev.scripts.devctl.governance.surfaces import SurfacePolicy
from dev.scripts.devctl.platform.contracts import (
    ArtifactSchemaSpec,
    ContractSpec,
    PlatformBlueprint,
)
from . import field_routes

_METADATA_FIELDS = frozenset({"schema_version", "contract_id", "command"})
_STARTUP_SURFACE_TOKENS = (
    "platform-contracts",
    "render-surfaces",
    "check_platform_contract_closure.py",
)
_RUNTIME_LAYER_PREFIXES = {
    "governance_runtime": ("dev.scripts.devctl.runtime.",),
}


def _import_symbol(target: str) -> object:
    module_name, _, attr_name = target.partition(":")
    if not module_name or not attr_name:
        raise ValueError(f"Invalid import target `{target}`.")
    module = import_module(module_name)
    return getattr(module, attr_name)


def _runtime_field_names(contract: ContractSpec) -> tuple[str, ...]:
    runtime_type = _import_symbol(contract.runtime_model)
    if not is_dataclass(runtime_type):
        raise TypeError(f"{contract.runtime_model} is not a dataclass type.")
    return tuple(
        field.name for field in fields(runtime_type) if field.name not in _METADATA_FIELDS
    )


def _surface_corpus(policy: SurfacePolicy) -> str:
    parts: list[str] = []
    parts.extend(policy.context.values())
    for surface in policy.surfaces:
        parts.extend(
            (
                surface.surface_id,
                surface.surface_type,
                surface.output_path,
                surface.description,
                *surface.required_contains,
            )
        )
    return "\n".join(parts)


def _check_runtime_contract(
    contract: ContractSpec,
) -> tuple[dict[str, object], dict[str, object] | None]:
    coverage: dict[str, object] = {
        "kind": "runtime_contract",
        "contract_id": contract.contract_id,
        "runtime_model": contract.runtime_model,
        "ok": True,
    }
    if not contract.runtime_model:
        coverage["detail"] = "No runtime model declared; skipped."
        return coverage, None

    module_name = contract.runtime_model.partition(":")[0]
    allowed_prefixes = _RUNTIME_LAYER_PREFIXES.get(contract.owner_layer)
    if allowed_prefixes and not any(module_name.startswith(prefix) for prefix in allowed_prefixes):
        detail = (
            f"Runtime model `{contract.runtime_model}` does not live under the "
            f"expected prefixes for owner layer `{contract.owner_layer}`."
        )
        coverage["ok"] = False
        coverage["detail"] = detail
        return coverage, {
            "kind": "runtime_contract",
            "contract_id": contract.contract_id,
            "rule": "owner-layer-runtime-path",
            "detail": detail,
        }

    expected_fields = tuple(field.name for field in contract.required_fields)
    actual_fields = _runtime_field_names(contract)
    missing_fields = tuple(sorted(set(expected_fields) - set(actual_fields)))
    extra_fields = tuple(sorted(set(actual_fields) - set(expected_fields)))
    if not missing_fields and not extra_fields:
        coverage["detail"] = "Platform contract row matches the runtime dataclass fields."
        coverage["expected_fields"] = expected_fields
        coverage["actual_fields"] = actual_fields
        return coverage, None

    detail = (
        "Runtime dataclass fields drift from the platform contract row."
        f" missing={missing_fields or 'none'} extra={extra_fields or 'none'}"
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    coverage["expected_fields"] = expected_fields
    coverage["actual_fields"] = actual_fields
    return coverage, {
        "kind": "runtime_contract",
        "contract_id": contract.contract_id,
        "rule": "runtime-field-drift",
        "missing_fields": missing_fields,
        "extra_fields": extra_fields,
        "detail": detail,
    }


def _check_artifact_schema(
    spec: ArtifactSchemaSpec,
) -> tuple[dict[str, object], dict[str, object] | None]:
    coverage: dict[str, object] = {
        "kind": "artifact_schema",
        "contract_id": spec.contract_id,
        "emitter_path": spec.emitter_path,
        "ok": True,
    }
    if not spec.compatibility_window or not spec.migration_path or not spec.rollback_path:
        detail = "Artifact schema row is missing compatibility or migration metadata."
        coverage["ok"] = False
        coverage["detail"] = detail
        return coverage, {
            "kind": "artifact_schema",
            "contract_id": spec.contract_id,
            "rule": "missing-matrix-metadata",
            "detail": detail,
        }

    module = import_module(spec.constants_module)
    contract_id_value = getattr(module, spec.contract_id_attr)
    schema_version_value = getattr(module, spec.schema_version_attr)
    if contract_id_value == spec.contract_id and schema_version_value == spec.schema_version:
        coverage["detail"] = "Artifact schema row matches the runtime/emitter constants."
        coverage["schema_version"] = spec.schema_version
        return coverage, None

    detail = (
        f"Artifact schema row drifted from {spec.constants_module}: "
        f"contract_id={contract_id_value!r} schema_version={schema_version_value!r}"
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    coverage["schema_version"] = spec.schema_version
    return coverage, {
        "kind": "artifact_schema",
        "contract_id": spec.contract_id,
        "rule": "artifact-schema-drift",
        "detail": detail,
    }


def _check_startup_surfaces(policy: SurfacePolicy) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    corpus = _surface_corpus(policy)
    missing = tuple(token for token in _STARTUP_SURFACE_TOKENS if token not in corpus)
    coverage = {
        "kind": "startup_surface",
        "surface_policy": policy.policy_path,
        "required_tokens": _STARTUP_SURFACE_TOKENS,
        "ok": not missing,
        "detail": (
            "Policy-owned startup surfaces expose the contract-routing tokens."
            if not missing
            else "Startup surfaces are missing required contract-routing tokens."
        ),
    }
    if not missing:
        return coverage, ()
    return coverage, (
        {
            "kind": "startup_surface",
            "rule": "missing-startup-surface-token",
            "missing_tokens": missing,
            "detail": "Policy-owned startup surfaces must expose the platform contract commands/guards.",
        },
    )


def _check_field_route_families(
    route_rows: tuple[dict[str, object], ...],
) -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    coverage_rows: list[dict[str, object]] = []
    violations: list[dict[str, object]] = []
    observed_route_ids: dict[tuple[str, str], set[str]] = {}
    passing_route_ids: dict[tuple[str, str], set[str]] = {}

    for row in route_rows:
        contract_id = str(row.get("contract_id") or "").strip()
        field_name = str(row.get("field_name") or "").strip()
        route_id = str(row.get("route_id") or "").strip()
        if not contract_id or not field_name or not route_id:
            continue
        key = (contract_id, field_name)
        observed_route_ids.setdefault(key, set()).add(route_id)
        if row.get("ok"):
            passing_route_ids.setdefault(key, set()).add(route_id)

    for key, expected_ids in field_routes.FIELD_ROUTE_FAMILY_REGISTRY.items():
        observed = tuple(sorted(observed_route_ids.get(key, set())))
        passing = tuple(sorted(passing_route_ids.get(key, set())))
        observed_set = set(observed)
        passing_set = set(passing)
        missing_route_ids = tuple(route_id for route_id in expected_ids if route_id not in observed_set)
        failing_route_ids = tuple(
            route_id for route_id in expected_ids if route_id in observed_set and route_id not in passing_set
        )
        ok = not missing_route_ids and not failing_route_ids
        coverage_rows.append(
            {
                "kind": "field_route_family",
                "contract_id": key[0],
                "field_name": key[1],
                "expected_route_ids": expected_ids,
                "observed_route_ids": observed,
                "passing_route_ids": passing,
                "ok": ok,
                "detail": (
                    "All declared consumers for the field route family are wired and verified."
                    if ok
                    else "Declared consumers for the field route family are missing or failing."
                ),
            }
        )
        if ok:
            continue
        violations.append(
            {
                "kind": "field_route_family",
                "contract_id": key[0],
                "field_name": key[1],
                "rule": "field-route-family-incomplete",
                "missing_route_ids": missing_route_ids,
                "failing_route_ids": failing_route_ids,
                "detail": (
                    f"Field route family {key[0]}.{key[1]} is incomplete."
                    f" missing={missing_route_ids or 'none'}"
                    f" failing={failing_route_ids or 'none'}"
                ),
            }
        )

    return tuple(coverage_rows), tuple(violations)


def evaluate_platform_contract_closure(
    blueprint: PlatformBlueprint,
    surface_policy: SurfacePolicy,
) -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    """Return closure coverage rows plus any platform contract violations."""
    coverage_rows: list[dict[str, object]] = []
    violations: list[dict[str, object]] = []

    for contract in blueprint.shared_contracts:
        if not contract.runtime_model:
            continue
        coverage, violation = _check_runtime_contract(contract)
        coverage_rows.append(coverage)
        if violation is not None:
            violations.append(violation)

    for spec in blueprint.artifact_schemas:
        coverage, violation = _check_artifact_schema(spec)
        coverage_rows.append(coverage)
        if violation is not None:
            violations.append(violation)

    coverage, surface_violations = _check_startup_surfaces(surface_policy)
    coverage_rows.append(coverage)
    violations.extend(surface_violations)

    from .emitter_parity import check_review_state_emitter_parity

    for parity_coverage, parity_violation in check_review_state_emitter_parity():
        coverage_rows.append(parity_coverage)
        if parity_violation is not None:
            violations.append(parity_violation)

    route_rows: list[dict[str, object]] = []
    for route_check in field_routes.FIELD_ROUTE_CHECKS:
        route_coverage, route_violation = route_check()
        route_rows.append(route_coverage)
        if route_violation is not None:
            violations.append(route_violation)
    coverage_rows.extend(route_rows)

    family_coverage, family_violations = _check_field_route_families(tuple(route_rows))
    coverage_rows.extend(family_coverage)
    violations.extend(family_violations)

    return tuple(coverage_rows), tuple(violations)
