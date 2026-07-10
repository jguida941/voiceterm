#!/usr/bin/env python3
"""Guard contract-registry uniqueness by contract id and schema version."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

_BOOT_ROOT = str(Path(__file__).resolve().parents[4])
if _BOOT_ROOT not in sys.path:
    sys.path.insert(0, _BOOT_ROOT)

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - package-style fallback for tests
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp

from dev.scripts.devctl.platform.contract_registry_models import (
    CONTRACT_REGISTRY_STORE_REL,
)
from dev.scripts.devctl.runtime.value_coercion import (
    coerce_int,
    coerce_string,
)

COMMAND = "check_contract_registry_composite_key_uniqueness"
CONTRACT_REGISTRY_COMPOSITE_KEY_UNIQUENESS_CONTRACT_ID = (
    "ContractRegistryCompositeKeyUniqueness"
)
POLICY_TODO_COMPOSITE_KEYS = {
    ("RustAuditReport", 1): (
        "dev/scripts/devctl/runtime/audit_report_contracts.py",
        "dev/scripts/devctl/rust_audit/report.py",
    ),
    ("SecurityReport", 1): (
        "dev/scripts/devctl/commands/security.py",
        "dev/scripts/devctl/runtime/audit_report_contracts.py",
    ),
}


@dataclass(frozen=True, slots=True)
class ContractRegistryCompositeKeyUniqueness:
    """Registry-facing contract for the composite-key uniqueness guard report."""

    command: str = COMMAND
    ok: bool = False
    registry_path: str = ""
    scan_count: int = 0
    duplicate_cluster_count: int = 0
    warning_count: int = 0
    policy_decision_required_count: int = 0
    violation_count: int = 0
    warnings: tuple[dict[str, object], ...] = field(default_factory=tuple)
    policy_todos: tuple[dict[str, object], ...] = field(default_factory=tuple)
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    schema_version: int = 1
    contract_id: str = CONTRACT_REGISTRY_COMPOSITE_KEY_UNIQUENESS_CONTRACT_ID


@dataclass(frozen=True, slots=True)
class ContractRegistryCompositeKeyUniquenessCommand:
    command: str = COMMAND
    shim_path: str = "dev/scripts/checks/check_contract_registry_composite_key_uniqueness.py"
    target_path: str = "dev/scripts/checks/contract_registry_composite_key_uniqueness/command.py"
    schema_version: int = 1
    contract_id: str = "ContractRegistryCompositeKeyUniquenessCommand"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RegistryRow:
    line_number: int
    contract_id: str
    schema_version: int
    entry_kind: str
    python_owner_path: str
    rust_owner_path: str
    fixture_path: str

    @property
    def owner_key(self) -> tuple[str, str]:
        return self.python_owner_path, self.rust_owner_path

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    registry_path: Path | None = None,
) -> dict[str, object]:
    """Return duplicate composite-key violations from the registry JSONL."""
    resolved_path = registry_path or (repo_root / CONTRACT_REGISTRY_STORE_REL)
    rows, load_errors = _load_rows(resolved_path)
    groups: dict[tuple[str, int], list[RegistryRow]] = {}
    for row in rows:
        groups.setdefault((row.contract_id, row.schema_version), []).append(row)

    warnings: list[dict[str, object]] = []
    policy_todos: list[dict[str, object]] = []
    violations: list[dict[str, object]] = list(load_errors)
    for (contract_id, schema_version), grouped in sorted(groups.items()):
        if len(grouped) <= 1:
            continue
        owner_keys = {row.owner_key for row in grouped}
        payload = _cluster_payload(
            contract_id=contract_id,
            schema_version=schema_version,
            grouped=grouped,
        )
        if len(owner_keys) == 1:
            warnings.append(
                {
                    **payload,
                    "rule": "same-owner-duplicate-registration",
                    "detail": (
                        "Duplicate contract/schema rows share one owner path; "
                        "dedupe registry emission or keep one canonical row."
                    ),
                }
            )
            continue
        if _known_policy_todo(
            contract_id=contract_id,
            schema_version=schema_version,
            grouped=grouped,
        ):
            policy_todos.append(
                {
                    **payload,
                    "rule": "policy-decision-required",
                    "policy_decision_required": True,
                    "detail": (
                        "Known forked registry ownership needs an operator policy "
                        "decision before the duplicate row can be retired."
                    ),
                }
            )
            continue
        violations.append(
            {
                **payload,
                "rule": "divergent-owner-composite-key",
                "policy_decision_required": True,
                "detail": (
                    "Duplicate contract/schema rows point at divergent owner paths; "
                    "choose one canonical owner path before this key can be unique."
                ),
            }
        )

    return {
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "registry_path": str(resolved_path),
        "scan_count": len(rows),
        "duplicate_cluster_count": len(warnings) + len(policy_todos) + len(
            [v for v in violations if v.get("rule") == "divergent-owner-composite-key"]
        ),
        "warning_count": len(warnings),
        "policy_decision_required_count": len(policy_todos),
        "violation_count": len(violations),
        "warnings": warnings,
        "policy_todos": policy_todos,
        "violations": violations,
    }


def _load_rows(path: Path) -> tuple[tuple[RegistryRow, ...], tuple[dict[str, object], ...]]:
    rows: list[RegistryRow] = []
    errors: list[dict[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return (), (
            {
                "rule": "registry-read-failed",
                "path": str(path),
                "detail": str(exc),
            },
        )
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(
                {
                    "rule": "registry-row-json-invalid",
                    "line_number": line_number,
                    "detail": str(exc),
                }
            )
            continue
        if not isinstance(payload, Mapping):
            errors.append(
                {
                    "rule": "registry-row-not-object",
                    "line_number": line_number,
                    "detail": "Registry rows must be JSON objects.",
                }
            )
            continue
        rows.append(_row_from_mapping(payload, line_number=line_number))
    return tuple(rows), tuple(errors)


def _row_from_mapping(payload: Mapping[str, object], *, line_number: int) -> RegistryRow:
    return RegistryRow(
        line_number=line_number,
        contract_id=coerce_string(payload.get("contract_id")),
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        entry_kind=coerce_string(payload.get("entry_kind")),
        python_owner_path=coerce_string(payload.get("python_owner_path")),
        rust_owner_path=coerce_string(payload.get("rust_owner_path")),
        fixture_path=coerce_string(payload.get("fixture_path")),
    )


def _cluster_payload(
    *,
    contract_id: str,
    schema_version: int,
    grouped: Iterable[RegistryRow],
) -> dict[str, object]:
    rows = tuple(grouped)
    return {
        "contract_id": contract_id,
        "schema_version": schema_version,
        "row_count": len(rows),
        "line_numbers": tuple(row.line_number for row in rows),
        "entry_kinds": tuple(row.entry_kind for row in rows),
        "owner_paths": tuple(sorted({row.python_owner_path for row in rows})),
        "rust_owner_paths": tuple(sorted({row.rust_owner_path for row in rows})),
        "fixture_paths": tuple(sorted({row.fixture_path for row in rows})),
        "rows": tuple(row.to_dict() for row in rows),
    }


def _known_policy_todo(
    *,
    contract_id: str,
    schema_version: int,
    grouped: Iterable[RegistryRow],
) -> bool:
    expected_owner_paths = POLICY_TODO_COMPOSITE_KEYS.get((contract_id, schema_version))
    if expected_owner_paths is None:
        return False
    observed_owner_paths = tuple(sorted({row.python_owner_path for row in grouped}))
    return observed_owner_paths == tuple(sorted(expected_owner_paths))


def _render_md(report: Mapping[str, object]) -> str:
    lines = ["# check_contract_registry_composite_key_uniqueness", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- scan_count: {report.get('scan_count', 0)}")
    lines.append(f"- duplicate_cluster_count: {report.get('duplicate_cluster_count', 0)}")
    lines.append(f"- warning_count: {report.get('warning_count', 0)}")
    lines.append(
        f"- policy_decision_required_count: {report.get('policy_decision_required_count', 0)}"
    )
    lines.append(f"- violation_count: {report.get('violation_count', 0)}")
    warnings = report.get("warnings")
    warnings = warnings if isinstance(warnings, list) else []
    if warnings:
        lines.extend(("", "## Warnings"))
        for warning in warnings:
            if isinstance(warning, Mapping):
                lines.append(_render_item(warning))
    policy_todos = report.get("policy_todos")
    policy_todos = policy_todos if isinstance(policy_todos, list) else []
    if policy_todos:
        lines.extend(("", "## Policy TODOs"))
        for policy_todo in policy_todos:
            if isinstance(policy_todo, Mapping):
                lines.append(_render_item(policy_todo))
    violations = report.get("violations")
    violations = violations if isinstance(violations, list) else []
    if violations:
        lines.extend(("", "## Violations"))
        for violation in violations:
            if isinstance(violation, Mapping):
                lines.append(_render_item(violation))
    return "\n".join(lines)


def _render_item(item: Mapping[str, object]) -> str:
    contract_id = item.get("contract_id") or item.get("path") or "unknown"
    schema_version = item.get("schema_version", "?")
    rule = item.get("rule", "unknown")
    detail = item.get("detail", "")
    line_numbers = item.get("line_numbers", ())
    owner_paths = item.get("owner_paths", ())
    suffix = ""
    if isinstance(line_numbers, (list, tuple)):
        suffix += f" lines={', '.join(str(value) for value in line_numbers)}"
    if isinstance(owner_paths, (list, tuple)):
        suffix += f" owners={', '.join(str(value) for value in owner_paths)}"
    return f"- `{contract_id}` v{schema_version} [{rule}]: {detail}{suffix}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--registry-path", type=Path)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    report = build_report(registry_path=args.registry_path)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
