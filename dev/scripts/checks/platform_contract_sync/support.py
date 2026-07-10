"""Shared helpers for platform-contract sync enforcement."""

from __future__ import annotations

from dataclasses import fields

from dev.scripts.devctl.platform.contracts import (
    CallerAuthoritySpec,
    ContractSpec,
    PlatformBlueprint,
    ServiceLifecycleSpec,
)

_SYNC_TARGETS = (
    (
        "service_lifecycle",
        "LocalServiceEndpoint",
        ServiceLifecycleSpec,
        frozenset({"notes"}),
    ),
    (
        "caller_authority",
        "CallerAuthorityPolicy",
        CallerAuthoritySpec,
        frozenset(),
    ),
)


def _field_names(contract: ContractSpec) -> tuple[str, ...]:
    return tuple(field.name for field in contract.required_fields)


def _spec_field_names(
    spec_type: type[ServiceLifecycleSpec] | type[CallerAuthoritySpec],
    *,
    excluded_fields: frozenset[str],
) -> tuple[str, ...]:
    return tuple(field.name for field in fields(spec_type) if field.name not in excluded_fields)


def evaluate_platform_contract_sync(
    blueprint: PlatformBlueprint,
) -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    """Return per-surface coverage rows plus any contract drift violations."""
    contract_map = {
        contract.contract_id: contract
        for contract in blueprint.shared_contracts
    }
    coverage_rows: list[dict[str, object]] = []
    violations: list[dict[str, object]] = []

    for surface_name, contract_id, spec_type, excluded_fields in _SYNC_TARGETS:
        surface_specs = getattr(blueprint, surface_name)
        expected_fields = _spec_field_names(spec_type, excluded_fields=excluded_fields)
        expected_set = set(expected_fields)
        contract = contract_map.get(contract_id)
        if contract is None:
            coverage_rows.append(
                {
                    "surface": surface_name,
                    "contract_id": contract_id,
                    "ok": False,
                    "expected_fields": expected_fields,
                    "actual_fields": (),
                    "detail": f"Missing shared contract `{contract_id}`.",
                }
            )
            violations.append(
                {
                    "surface": surface_name,
                    "contract_id": contract_id,
                    "rule": "missing-contract",
                    "missing_fields": expected_fields,
                    "extra_fields": (),
                    "detail": f"`{surface_name}` has no shared contract row `{contract_id}`.",
                }
            )
            continue

        actual_fields = _field_names(contract)
        actual_set = set(actual_fields)
        missing_fields = tuple(sorted(expected_set - actual_set))
        extra_fields = tuple(sorted(actual_set - expected_set))
        empty_surface = len(surface_specs) == 0
        ok = not empty_surface and not missing_fields and not extra_fields
        detail_parts: list[str] = []
        if empty_surface:
            detail_parts.append(f"`{surface_name}` has no spec rows.")
        if missing_fields:
            detail_parts.append(f"missing fields: {', '.join(missing_fields)}")
        if extra_fields:
            detail_parts.append(f"extra fields: {', '.join(extra_fields)}")
        detail = "; ".join(detail_parts) if detail_parts else "Contract and surface stay aligned."
        coverage_rows.append(
            {
                "surface": surface_name,
                "contract_id": contract_id,
                "ok": ok,
                "expected_fields": expected_fields,
                "actual_fields": actual_fields,
                "detail": detail,
            }
        )
        if ok:
            continue
        violations.append(
            {
                "surface": surface_name,
                "contract_id": contract_id,
                "rule": "field-drift" if (missing_fields or extra_fields) else "empty-surface",
                "missing_fields": missing_fields,
                "extra_fields": extra_fields,
                "detail": detail,
            }
        )

    return tuple(coverage_rows), tuple(violations)
