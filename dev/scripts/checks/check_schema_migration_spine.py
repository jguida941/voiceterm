#!/usr/bin/env python3
"""Validate schema migration and store-authority policy for durable contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.platform.schema_migration_spine import (  # noqa: E402
    SchemaMigrationViolation,
    durable_schema_policies,
    evaluate_schema_migration_spine,
)


def build_report(*, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    _ = repo_root
    coverage, violations = evaluate_schema_migration_spine()
    return {
        **coverage,
        "policies": [policy.to_dict() for policy in durable_schema_policies()],
        "violations": _serialized_violations(violations),
    }


def _serialized_violations(
    violations: tuple[SchemaMigrationViolation, ...],
) -> list[dict[str, str]]:
    return [violation.to_dict() for violation in violations]


def render_md(report: dict[str, object]) -> str:
    lines = ["# check_schema_migration_spine", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- durable_contract_count: {report.get('durable_contract_count', 0)}")
    lines.append(f"- policy_count: {report.get('policy_count', 0)}")
    lines.append(f"- artifact_schema_count: {report.get('artifact_schema_count', 0)}")
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
