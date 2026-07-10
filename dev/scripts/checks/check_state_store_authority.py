#!/usr/bin/env python3
"""Validate registered durable stores route through state-store authority."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from dataclasses import asdict, dataclass

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.platform.schema_migration_spine import (  # noqa: E402
    NON_BLOCKING_STORE_AUTHORITY_STATUSES,
    DurableSchemaPolicy,
    durable_schema_policies,
)

_STATE_STORE_TOKENS = frozenset(
    {
        "append_json_mapping",
        "append_json_mappings",
        "replace_json_mappings",
        "transform_json_mappings",
        "state_store_authority",
    }
)


@dataclass(frozen=True, slots=True)
class StateStoreAuthorityViolation:
    rule: str
    contract_id: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def evaluate_state_store_authority(
    *,
    policies: tuple[DurableSchemaPolicy, ...] | None = None,
) -> tuple[dict[str, object], tuple[StateStoreAuthorityViolation, ...]]:
    policies = policies or durable_schema_policies()
    violations: list[StateStoreAuthorityViolation] = []
    registered: list[DurableSchemaPolicy] = []
    planned: list[DurableSchemaPolicy] = []
    writer_refs: list[dict[str, str]] = []

    for policy in policies:
        if policy.store_authority_status in NON_BLOCKING_STORE_AUTHORITY_STATUSES:
            planned.append(policy)
            continue
        registered.append(policy)
        target, source_path, error = _resolve_writer(policy.store_authority)
        if error:
            violations.append(
                StateStoreAuthorityViolation(
                    rule="registered-store-writer-unresolvable",
                    contract_id=policy.contract_id,
                    detail=error,
                )
            )
            continue
        source = _source_for(target)
        if not any(token in source for token in _STATE_STORE_TOKENS):
            violations.append(
                StateStoreAuthorityViolation(
                    rule="registered-store-writer-not-state-store-backed",
                    contract_id=policy.contract_id,
                    detail=(
                        "Registered store writer must call or wrap the shared "
                        "state_store_authority helpers."
                    ),
                )
            )
            continue
        writer_refs.append(
            {
                "contract_id": policy.contract_id,
                "store_path": policy.store_path,
                "writer_ref": policy.store_authority,
                "source_path": source_path,
            }
        )

    coverage = {
        "command": "check_state_store_authority",
        "schema_version": 1,
        "policy_count": len(policies),
        "registered_policy_count": len(registered),
        "planned_policy_count": len(planned),
        "planned_policy_contract_ids": [policy.contract_id for policy in planned],
        "registered_writer_refs": writer_refs,
        "ok": not violations,
    }
    return coverage, tuple(violations)


def _resolve_writer(ref: str) -> tuple[object | None, str, str]:
    module_name, _, attr_name = ref.partition(":")
    if not module_name or not attr_name:
        return None, "", f"Invalid writer ref `{ref}`; expected module:attribute."
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - exact import errors vary.
        return None, "", f"Unable to import writer module `{module_name}`: {exc}"
    try:
        target = getattr(module, attr_name)
    except AttributeError:
        return None, inspect.getsourcefile(module) or "", (
            f"Writer attribute `{attr_name}` missing from `{module_name}`."
        )
    return target, inspect.getsourcefile(target) or inspect.getsourcefile(module) or "", ""


def _source_for(target: object | None) -> str:
    if target is None:
        return ""
    try:
        return inspect.getsource(target)
    except (OSError, TypeError):
        return ""


def build_report() -> dict[str, object]:
    coverage, violations = evaluate_state_store_authority()
    return {
        **coverage,
        "violations": [violation.to_dict() for violation in violations],
    }


def render_md(report: dict[str, object]) -> str:
    lines = ["# check_state_store_authority", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- policy_count: {report.get('policy_count', 0)}")
    lines.append(f"- registered_policy_count: {report.get('registered_policy_count', 0)}")
    planned = report.get("planned_policy_contract_ids", [])
    if isinstance(planned, list):
        lines.append(f"- planned_policy_count: {len(planned)}")
        if planned:
            lines.append("- planned_policy_contract_ids: " + ", ".join(map(str, planned)))
    violations = report.get("violations", [])
    lines.append(f"- violations: {len(violations) if isinstance(violations, list) else 0}")
    if isinstance(violations, list) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                f"- `{violation.get('contract_id')}` [{violation.get('rule')}]: "
                f"{violation.get('detail')}"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
