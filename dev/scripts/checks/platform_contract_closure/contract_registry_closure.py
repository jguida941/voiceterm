"""Closure checks for the repo-owned platform contract registry."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.config import REPO_ROOT
from dev.scripts.devctl.platform.blueprint import build_platform_blueprint
from dev.scripts.devctl.platform.contract_registry import (
    build_contract_registry_rows,
    contract_registry_path,
    read_contract_registry_rows,
)
from dev.scripts.devctl.platform.contract_registry_models import ContractRegistryRow
from dev.scripts.devctl.platform.contracts import PlatformBlueprint


def check_contract_registry_closure(
    *,
    repo_root: Path = REPO_ROOT,
    blueprint: PlatformBlueprint | None = None,
    rows: tuple[ContractRegistryRow, ...] | None = None,
) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    """Return coverage and violations for the repo-owned contract registry."""
    blueprint = blueprint or build_platform_blueprint()
    expected_rows = build_contract_registry_rows(blueprint)
    registry_path = contract_registry_path(repo_root)
    coverage: dict[str, object] = {
        "kind": "contract_registry",
        "contract_id": "PlatformContractRegistry",
        "registry_path": str(registry_path),
        "expected_row_count": len(expected_rows),
        "ok": True,
    }
    if rows is None:
        if not registry_path.exists():
            coverage["ok"] = False
            coverage["observed_row_count"] = 0
            coverage["detail"] = "Repo-owned platform contract registry is missing."
            return coverage, (
                {
                    "kind": "contract_registry",
                    "contract_id": "PlatformContractRegistry",
                    "rule": "missing-contract-registry",
                    "detail": f"Missing registry file `{registry_path}`.",
                },
            )
        rows = read_contract_registry_rows(registry_path)

    observed_by_key: dict[tuple[str, str], ContractRegistryRow] = {}
    violations: list[dict[str, object]] = []
    for row in rows:
        key = row.key()
        if key in observed_by_key:
            violations.append(
                {
                    "kind": "contract_registry",
                    "contract_id": row.registered_contract_id,
                    "rule": "duplicate-registry-row",
                    "detail": (
                        "Contract registry rows must be unique per "
                        f"`(entry_kind, contract_id)`; duplicate={key!r}."
                    ),
                }
            )
            continue
        observed_by_key[key] = row

    expected_by_key = {row.key(): row for row in expected_rows}
    for key, expected in expected_by_key.items():
        observed = observed_by_key.get(key)
        if observed is None:
            violations.append(
                {
                    "kind": "contract_registry",
                    "contract_id": expected.registered_contract_id,
                    "rule": "missing-registry-row",
                    "detail": (
                        "Registry row missing for "
                        f"{expected.entry_kind}:{expected.registered_contract_id}."
                    ),
                }
            )
            continue
        stale_fields = _stale_fields(expected, observed)
        if stale_fields:
            violations.append(
                {
                    "kind": "contract_registry",
                    "contract_id": expected.registered_contract_id,
                    "rule": "stale-registry-row",
                    "detail": (
                        "Registry row drifted from the current platform blueprint. "
                        f"stale_fields={', '.join(stale_fields)}"
                    ),
                    "stale_fields": stale_fields,
                }
            )

    for key, observed in observed_by_key.items():
        if key in expected_by_key:
            continue
        violations.append(
            {
                "kind": "contract_registry",
                "contract_id": observed.registered_contract_id,
                "rule": "extra-registry-row",
                "detail": (
                    "Registry row has no matching blueprint contract or artifact schema: "
                    f"{observed.entry_kind}:{observed.registered_contract_id}."
                ),
            }
        )

    coverage["observed_row_count"] = len(rows)
    coverage["violation_count"] = len(violations)
    coverage["detail"] = (
        "Repo-owned contract registry matches the current platform blueprint."
        if not violations
        else "Repo-owned contract registry drifted from the current platform blueprint."
    )
    coverage["ok"] = not violations
    return coverage, tuple(violations)


def _stale_fields(
    expected: ContractRegistryRow,
    observed: ContractRegistryRow,
) -> tuple[str, ...]:
    stale: list[str] = []
    for field_name in (
        "entry_kind",
        "python_owner_path",
        "rust_owner_path",
        "fixture_path",
        "registered_schema_version",
        "ownership_mode",
        "parity_command",
        "registry_path",
    ):
        if getattr(expected, field_name) != getattr(observed, field_name):
            stale.append(field_name)
    return tuple(stale)


__all__ = ["check_contract_registry_closure"]
