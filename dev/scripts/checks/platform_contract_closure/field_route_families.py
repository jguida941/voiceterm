"""Field-route family completeness checks for platform closure."""

from __future__ import annotations

from . import field_routes


def check_field_route_families(
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
        coverage, violation = _field_route_family_result(
            key=key,
            expected_ids=expected_ids,
            observed_route_ids=observed_route_ids,
            passing_route_ids=passing_route_ids,
        )
        coverage_rows.append(coverage)
        if violation is not None:
            violations.append(violation)
    return tuple(coverage_rows), tuple(violations)


def _field_route_family_result(
    *,
    key: tuple[str, str],
    expected_ids: tuple[str, ...],
    observed_route_ids: dict[tuple[str, str], set[str]],
    passing_route_ids: dict[tuple[str, str], set[str]],
) -> tuple[dict[str, object], dict[str, object] | None]:
    observed = tuple(sorted(observed_route_ids.get(key, set())))
    passing = tuple(sorted(passing_route_ids.get(key, set())))
    missing_route_ids = tuple(route_id for route_id in expected_ids if route_id not in observed)
    failing_route_ids = tuple(
        route_id for route_id in expected_ids if route_id in observed and route_id not in passing
    )
    ok = not missing_route_ids and not failing_route_ids
    coverage = {
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
    if ok:
        return coverage, None
    return coverage, {
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
