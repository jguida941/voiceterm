#!/usr/bin/env python3
"""Validate managed check CLIs and focused tests share one evaluator contract."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.governance.script_catalog_registry import (  # noqa: E402
    CHECK_SCRIPT_RELATIVE_PATHS,
)


@dataclass(frozen=True, slots=True)
class CheckCliTestParityTarget:
    check_id: str
    check_script_path: str
    cli_contract_paths: tuple[str, ...]
    test_contract_paths: tuple[str, ...]
    shared_tokens: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CheckCliTestParityViolation:
    rule: str
    check_id: str
    path: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def managed_parity_targets() -> tuple[CheckCliTestParityTarget, ...]:
    return (
        CheckCliTestParityTarget(
            check_id="platform_contract_closure",
            check_script_path="dev/scripts/checks/check_platform_contract_closure.py",
            cli_contract_paths=(
                "dev/scripts/checks/check_platform_contract_closure.py",
                "dev/scripts/checks/platform_contract_closure/command.py",
            ),
            test_contract_paths=(
                "dev/scripts/devctl/tests/checks/platform_contract_closure/"
                "test_check_platform_contract_closure.py",
            ),
            shared_tokens=("platform_contract_closure.report", "build_report"),
        ),
        CheckCliTestParityTarget(
            check_id="schema_fixture_handshake",
            check_script_path="dev/scripts/checks/check_schema_fixture_handshake.py",
            cli_contract_paths=("dev/scripts/checks/check_schema_fixture_handshake.py",),
            test_contract_paths=(
                "dev/scripts/devctl/tests/checks/test_check_schema_fixture_handshake.py",
            ),
            shared_tokens=("evaluate_schema_fixture_handshake",),
        ),
        CheckCliTestParityTarget(
            check_id="schema_version_monotonic",
            check_script_path="dev/scripts/checks/check_schema_version_monotonic.py",
            cli_contract_paths=("dev/scripts/checks/check_schema_version_monotonic.py",),
            test_contract_paths=(
                "dev/scripts/devctl/tests/checks/test_check_schema_fixture_handshake.py",
            ),
            shared_tokens=("evaluate_schema_version_monotonic",),
        ),
        CheckCliTestParityTarget(
            check_id="schema_migration_spine",
            check_script_path="dev/scripts/checks/check_schema_migration_spine.py",
            cli_contract_paths=("dev/scripts/checks/check_schema_migration_spine.py",),
            test_contract_paths=(
                "dev/scripts/devctl/tests/checks/test_check_schema_migration_spine.py",
            ),
            shared_tokens=("evaluate_schema_migration_spine",),
        ),
        CheckCliTestParityTarget(
            check_id="state_store_authority",
            check_script_path="dev/scripts/checks/check_state_store_authority.py",
            cli_contract_paths=("dev/scripts/checks/check_state_store_authority.py",),
            test_contract_paths=(
                "dev/scripts/devctl/tests/checks/test_check_state_store_authority.py",
            ),
            shared_tokens=("evaluate_state_store_authority",),
        ),
        CheckCliTestParityTarget(
            check_id="check_cli_test_parity",
            check_script_path="dev/scripts/checks/check_check_cli_test_parity.py",
            cli_contract_paths=("dev/scripts/checks/check_check_cli_test_parity.py",),
            test_contract_paths=(
                "dev/scripts/devctl/tests/checks/test_check_check_cli_test_parity.py",
            ),
            shared_tokens=("evaluate_check_cli_test_parity",),
        ),
    )


def evaluate_check_cli_test_parity(
    *,
    repo_root: Path = REPO_ROOT,
    targets: tuple[CheckCliTestParityTarget, ...] | None = None,
    catalog_paths: Mapping[str, str] | None = None,
) -> tuple[dict[str, object], tuple[CheckCliTestParityViolation, ...]]:
    selected_targets = targets or managed_parity_targets()
    catalog = catalog_paths or CHECK_SCRIPT_RELATIVE_PATHS
    violations: list[CheckCliTestParityViolation] = []
    target_reports: list[dict[str, object]] = []

    for target in selected_targets:
        target_violations: list[CheckCliTestParityViolation] = []
        catalog_path = catalog.get(target.check_id, "")
        if not catalog_path:
            target_violations.append(
                CheckCliTestParityViolation(
                    rule="unregistered-check",
                    check_id=target.check_id,
                    path=target.check_script_path,
                    detail="Managed check must be registered in the script catalog.",
                )
            )
        elif catalog_path != target.check_script_path:
            target_violations.append(
                CheckCliTestParityViolation(
                    rule="registered-check-path-drift",
                    check_id=target.check_id,
                    path=target.check_script_path,
                    detail=(
                        f"Script catalog maps check to {catalog_path!r}; "
                        f"expected {target.check_script_path!r}."
                    ),
                )
            )

        cli_text, cli_path_violations = _combined_text(
            repo_root=repo_root,
            check_id=target.check_id,
            paths=target.cli_contract_paths,
            rule="missing-cli-contract-path",
        )
        test_text, test_path_violations = _combined_text(
            repo_root=repo_root,
            check_id=target.check_id,
            paths=target.test_contract_paths,
            rule="missing-test-contract-path",
        )
        target_violations.extend(cli_path_violations)
        target_violations.extend(test_path_violations)

        for token in target.shared_tokens:
            if token not in cli_text:
                target_violations.append(
                    CheckCliTestParityViolation(
                        rule="cli-shared-token-missing",
                        check_id=target.check_id,
                        path=", ".join(target.cli_contract_paths),
                        detail=f"CLI contract path must reference shared token {token!r}.",
                    )
                )
            if token not in test_text:
                target_violations.append(
                    CheckCliTestParityViolation(
                        rule="test-shared-token-missing",
                        check_id=target.check_id,
                        path=", ".join(target.test_contract_paths),
                        detail=f"Focused test path must reference shared token {token!r}.",
                    )
                )

        violations.extend(target_violations)
        target_reports.append(
            {
                **target.to_dict(),
                "catalog_path": catalog_path,
                "ok": not target_violations,
                "violation_count": len(target_violations),
            }
        )

    coverage = {
        "command": "check_check_cli_test_parity",
        "schema_version": 1,
        "managed_target_count": len(selected_targets),
        "ok_target_count": sum(1 for target in target_reports if target["ok"]),
        "targets": target_reports,
        "ok": not violations,
    }
    return coverage, tuple(violations)


def _combined_text(
    *,
    repo_root: Path,
    check_id: str,
    paths: tuple[str, ...],
    rule: str,
) -> tuple[str, tuple[CheckCliTestParityViolation, ...]]:
    chunks: list[str] = []
    violations: list[CheckCliTestParityViolation] = []
    for relative in paths:
        path = repo_root / relative
        if not path.is_file():
            violations.append(
                CheckCliTestParityViolation(
                    rule=rule,
                    check_id=check_id,
                    path=relative,
                    detail="Expected parity contract file is missing.",
                )
            )
            continue
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks), tuple(violations)


def build_report(*, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    coverage, violations = evaluate_check_cli_test_parity(repo_root=repo_root)
    return {
        **coverage,
        "violations": [violation.to_dict() for violation in violations],
    }


def render_md(report: dict[str, object]) -> str:
    lines = ["# check_check_cli_test_parity", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- managed_target_count: {report.get('managed_target_count', 0)}")
    lines.append(f"- ok_target_count: {report.get('ok_target_count', 0)}")
    violations = report.get("violations", [])
    lines.append(f"- violations: {len(violations) if isinstance(violations, list) else 0}")
    if isinstance(violations, list) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                f"- `{violation.get('check_id')}` [{violation.get('rule')}]: "
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
