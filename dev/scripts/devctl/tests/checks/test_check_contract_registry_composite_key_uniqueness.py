"""Tests for contract-registry composite-key uniqueness guard."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.checks.contract_registry_composite_key_uniqueness.command import (
    build_report,
)


def _write_registry(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _row(
    contract_id: str,
    entry_kind: str,
    owner_path: str,
    *,
    schema_version: int = 1,
) -> dict[str, object]:
    return {
        "contract_id": contract_id,
        "entry_kind": entry_kind,
        "fixture_path": f"dev/test_data/schema_fixtures/{contract_id}/{schema_version}",
        "ownership_mode": "python_only",
        "parity_command": "python3 dev/scripts/checks/check_platform_contract_closure.py --format json",
        "python_owner_path": owner_path,
        "registry_path": "dev/state/contract_registry.jsonl",
        "registry_row_contract_id": "PlatformContractRegistryRow",
        "registry_row_schema_version": 1,
        "rust_owner_path": "",
        "schema_version": schema_version,
    }


def test_same_owner_duplicate_is_warning_not_failure(tmp_path: Path) -> None:
    registry_path = tmp_path / "contract_registry.jsonl"
    _write_registry(
        registry_path,
        [
            _row("DemoReceipt", "artifact_schema", "dev/runtime/demo.py"),
            _row("DemoReceipt", "shared_contract", "dev/runtime/demo.py"),
        ],
    )

    report = build_report(registry_path=registry_path)

    assert report["ok"] is True
    assert report["warning_count"] == 1
    assert report["violation_count"] == 0
    assert report["warnings"][0]["rule"] == "same-owner-duplicate-registration"


def test_divergent_owner_duplicate_requires_policy_decision(tmp_path: Path) -> None:
    registry_path = tmp_path / "contract_registry.jsonl"
    _write_registry(
        registry_path,
        [
            _row("DemoReport", "artifact_schema", "dev/commands/demo.py"),
            _row("DemoReport", "shared_contract", "dev/runtime/demo.py"),
        ],
    )

    report = build_report(registry_path=registry_path)

    assert report["ok"] is False
    assert report["warning_count"] == 0
    assert report["violation_count"] == 1
    assert report["violations"][0]["rule"] == "divergent-owner-composite-key"
    assert report["violations"][0]["policy_decision_required"] is True


def test_current_repo_flags_only_policy_forks_after_safe_dedup() -> None:
    report = build_report()

    assert report["ok"] is True
    assert report["warning_count"] == 0
    assert report["policy_decision_required_count"] == 2
    assert report["violation_count"] == 0
    assert {
        todo["contract_id"]
        for todo in report["policy_todos"]
        if todo["rule"] == "policy-decision-required"
    } == {"RustAuditReport", "SecurityReport"}
