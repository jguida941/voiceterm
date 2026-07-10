#!/usr/bin/env python3
"""Ensure registered schema versions have matching fixture roots."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.checks.check_schema_fixture_handshake import (  # noqa: E402
    evaluate_schema_fixture_handshake,
)
from dev.scripts.devctl.platform.contract_registry import (  # noqa: E402
    contract_registry_path,
    read_contract_registry_rows,
)


@dataclass(frozen=True, slots=True)
class SchemaVersionViolation:
    rule: str
    contract_id: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def evaluate_schema_version_monotonic(
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, object], tuple[SchemaVersionViolation, ...]]:
    rows = read_contract_registry_rows(contract_registry_path(repo_root))
    violations: list[SchemaVersionViolation] = []
    for row in rows:
        expected_suffix = f"/{row.registered_schema_version}"
        if row.fixture_path.endswith(expected_suffix):
            continue
        violations.append(
            SchemaVersionViolation(
                rule="fixture-path-version-drift",
                contract_id=row.registered_contract_id,
                detail=(
                    f"fixture_path must end with registered schema version "
                    f"{expected_suffix!r}; got {row.fixture_path!r}."
                ),
            )
        )

    fixture_coverage, fixture_violations = evaluate_schema_fixture_handshake(
        repo_root=repo_root
    )
    for violation in fixture_violations:
        violations.append(
            SchemaVersionViolation(
                rule=f"fixture-handshake:{violation.rule}",
                contract_id=violation.contract_id,
                detail=violation.detail,
            )
        )

    coverage = {
        "command": "check_schema_version_monotonic",
        "schema_version": 1,
        "registry_row_count": len(rows),
        "fixture_roots_checked": fixture_coverage.get("fixture_roots_checked", 0),
        "ok": not violations,
    }
    return coverage, tuple(violations)


def build_report(*, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    coverage, violations = evaluate_schema_version_monotonic(repo_root=repo_root)
    return {
        **coverage,
        "violations": [violation.to_dict() for violation in violations],
    }


def render_md(report: dict[str, object]) -> str:
    lines = ["# check_schema_version_monotonic", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- registry_row_count: {report.get('registry_row_count', 0)}")
    lines.append(f"- fixture_roots_checked: {report.get('fixture_roots_checked', 0)}")
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
