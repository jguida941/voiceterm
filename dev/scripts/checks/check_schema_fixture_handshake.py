#!/usr/bin/env python3
"""Validate registered schema fixture handshakes for platform contracts."""

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

from dev.scripts.devctl.platform.contract_registry import (  # noqa: E402
    contract_registry_path,
    read_contract_registry_rows,
)
from dev.scripts.devctl.platform.contract_registry_models import (  # noqa: E402
    ContractRegistryRow,
)

SCHEMA_FIXTURE_CONTRACT_ID = "PlatformSchemaFixture"
SCHEMA_FIXTURE_VERSION = 1
REQUIRED_INVALID_REASONS = frozenset(
    {
        "missing_required_field",
        "schema_version_mismatch",
    }
)


@dataclass(frozen=True, slots=True)
class SchemaFixtureViolation:
    rule: str
    contract_id: str
    path: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def evaluate_schema_fixture_handshake(
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, object], tuple[SchemaFixtureViolation, ...]]:
    registry_path = contract_registry_path(repo_root)
    rows = read_contract_registry_rows(registry_path)
    violations: list[SchemaFixtureViolation] = []
    fixture_roots_checked = 0
    valid_fixtures_checked = 0
    invalid_fixtures_checked = 0

    for row in rows:
        root = repo_root / row.fixture_path
        valid_dir = root / "valid"
        invalid_dir = root / "invalid"
        if not root.is_dir():
            violations.append(
                _violation(row, root, "missing-fixture-root", "Fixture root missing.")
            )
            continue
        fixture_roots_checked += 1
        valid_files = _json_files(valid_dir)
        invalid_files = _json_files(invalid_dir)
        if not valid_files:
            violations.append(
                _violation(
                    row,
                    valid_dir,
                    "missing-valid-fixture",
                    "Fixture root must contain at least one valid/*.json file.",
                )
            )
        if not invalid_files:
            violations.append(
                _violation(
                    row,
                    invalid_dir,
                    "missing-invalid-fixture",
                    "Fixture root must contain invalid/*.json examples.",
                )
            )

        for fixture_path in valid_files:
            valid_fixtures_checked += 1
            violations.extend(_validate_fixture(row, fixture_path, expected_role="valid"))
        invalid_reasons: set[str] = set()
        for fixture_path in invalid_files:
            invalid_fixtures_checked += 1
            fixture_violations, reason = _validate_invalid_fixture(row, fixture_path)
            violations.extend(fixture_violations)
            if reason:
                invalid_reasons.add(reason)
        missing_reasons = sorted(REQUIRED_INVALID_REASONS - invalid_reasons)
        if missing_reasons:
            violations.append(
                _violation(
                    row,
                    invalid_dir,
                    "missing-invalid-reason",
                    "Invalid fixtures must cover: " + ", ".join(missing_reasons),
                )
            )

    coverage = {
        "command": "check_schema_fixture_handshake",
        "schema_version": 1,
        "registry_path": str(registry_path.relative_to(repo_root)),
        "registry_row_count": len(rows),
        "fixture_roots_checked": fixture_roots_checked,
        "valid_fixtures_checked": valid_fixtures_checked,
        "invalid_fixtures_checked": invalid_fixtures_checked,
        "ok": not violations,
    }
    return coverage, tuple(violations)


def _validate_invalid_fixture(
    row: ContractRegistryRow,
    fixture_path: Path,
) -> tuple[tuple[SchemaFixtureViolation, ...], str]:
    violations = list(_validate_fixture(row, fixture_path, expected_role="invalid"))
    payload = _load_json(fixture_path)
    reason = ""
    if isinstance(payload, dict):
        reason = _text(payload.get("invalid_reason"))
        if reason == "schema_version_mismatch":
            observed_version = payload.get("schema_version")
            if observed_version == row.registered_schema_version:
                violations.append(
                    _violation(
                        row,
                        fixture_path,
                        "invalid-schema-version-not-mismatched",
                        "schema_version_mismatch fixture must not use the registered schema version.",
                    )
                )
    return tuple(violations), reason


def _validate_fixture(
    row: ContractRegistryRow,
    fixture_path: Path,
    *,
    expected_role: str,
) -> tuple[SchemaFixtureViolation, ...]:
    payload = _load_json(fixture_path)
    if not isinstance(payload, dict):
        return (
            _violation(
                row,
                fixture_path,
                "invalid-json-fixture",
                "Fixture must be a JSON object.",
            ),
        )
    violations: list[SchemaFixtureViolation] = []
    expected_result = "accept" if expected_role == "valid" else "reject"
    expected_fields = {
        "schema_fixture_contract_id": SCHEMA_FIXTURE_CONTRACT_ID,
        "schema_fixture_version": SCHEMA_FIXTURE_VERSION,
        "fixture_role": expected_role,
        "expected_result": expected_result,
        "contract_id": row.registered_contract_id,
        "entry_kind": row.entry_kind,
    }
    for field_name, expected_value in expected_fields.items():
        if payload.get(field_name) == expected_value:
            continue
        violations.append(
            _violation(
                row,
                fixture_path,
                "fixture-field-drift",
                f"{field_name} expected {expected_value!r}, got {payload.get(field_name)!r}.",
            )
        )
    if expected_role == "valid" and payload.get("schema_version") != row.registered_schema_version:
        violations.append(
            _violation(
                row,
                fixture_path,
                "valid-schema-version-drift",
                "Valid fixture schema_version must match the registry row.",
            )
        )
    return tuple(violations)


def _json_files(path: Path) -> tuple[Path, ...]:
    if not path.is_dir():
        return ()
    return tuple(sorted(candidate for candidate in path.glob("*.json") if candidate.is_file()))


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _text(value: object) -> str:
    return str(value or "").strip()


def _violation(
    row: ContractRegistryRow,
    path: Path,
    rule: str,
    detail: str,
) -> SchemaFixtureViolation:
    return SchemaFixtureViolation(
        rule=rule,
        contract_id=row.registered_contract_id,
        path=str(path),
        detail=detail,
    )


def build_report(*, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    coverage, violations = evaluate_schema_fixture_handshake(repo_root=repo_root)
    return {
        **coverage,
        "violations": [violation.to_dict() for violation in violations],
    }


def render_md(report: dict[str, object]) -> str:
    lines = ["# check_schema_fixture_handshake", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- registry_row_count: {report.get('registry_row_count', 0)}")
    lines.append(f"- fixture_roots_checked: {report.get('fixture_roots_checked', 0)}")
    lines.append(f"- valid_fixtures_checked: {report.get('valid_fixtures_checked', 0)}")
    lines.append(f"- invalid_fixtures_checked: {report.get('invalid_fixtures_checked', 0)}")
    violations = report.get("violations", [])
    lines.append(f"- violations: {len(violations) if isinstance(violations, list) else 0}")
    if isinstance(violations, list) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                f"- `{violation.get('contract_id')}` [{violation.get('rule')}]: "
                f"{violation.get('detail')} ({violation.get('path')})"
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
