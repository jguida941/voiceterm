"""Tests for the schema-fixture handshake guard."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from dev.scripts.checks.schema_fixture_handshake.command import (
    evaluate_schema_fixture_handshake,
)
from dev.scripts.checks.check_schema_version_monotonic import (
    evaluate_schema_version_monotonic,
)


def test_schema_fixture_handshake_passes_current_repo() -> None:
    coverage, violations = evaluate_schema_fixture_handshake()

    assert coverage["ok"] is True
    assert coverage["registry_row_count"] >= 1
    assert coverage["fixture_roots_checked"] == coverage["registry_row_count"]
    assert coverage["valid_fixtures_checked"] >= coverage["registry_row_count"]
    assert coverage["invalid_fixtures_checked"] >= coverage["registry_row_count"] * 2
    assert violations == ()


def test_schema_fixture_handshake_flags_missing_invalid_reason(tmp_path: Path) -> None:
    registry_path = tmp_path / "dev/state/contract_registry.jsonl"
    registry_path.parent.mkdir(parents=True)
    row = {
        "contract_id": "DemoContract",
        "entry_kind": "shared_contract",
        "python_owner_path": "dev/demo.py",
        "rust_owner_path": "",
        "fixture_path": "dev/test_data/schema_fixtures/DemoContract/1",
        "schema_version": 1,
        "ownership_mode": "python_only",
        "parity_command": "python3 dev/scripts/checks/check_schema_fixture_handshake.py --format json",
        "registry_path": "dev/state/contract_registry.jsonl",
        "registry_row_contract_id": "PlatformContractRegistryRow",
        "registry_row_schema_version": 1,
    }
    registry_path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
    root = tmp_path / row["fixture_path"]
    (root / "valid").mkdir(parents=True)
    (root / "invalid").mkdir()
    valid = {
        "schema_fixture_contract_id": "PlatformSchemaFixture",
        "schema_fixture_version": 1,
        "fixture_role": "valid",
        "expected_result": "accept",
        "contract_id": "DemoContract",
        "entry_kind": "shared_contract",
        "schema_version": 1,
    }
    invalid = {
        **valid,
        "fixture_role": "invalid",
        "expected_result": "reject",
        "invalid_reason": "schema_version_mismatch",
        "schema_version": 2,
    }
    (root / "valid/registry-row.json").write_text(
        json.dumps(valid, sort_keys=True),
        encoding="utf-8",
    )
    (root / "invalid/schema-version-mismatch.json").write_text(
        json.dumps(invalid, sort_keys=True),
        encoding="utf-8",
    )

    coverage, violations = evaluate_schema_fixture_handshake(repo_root=tmp_path)

    assert coverage["ok"] is False
    assert any(
        violation.rule == "missing-invalid-reason"
        and "missing_required_field" in violation.detail
        for violation in violations
    )


def test_schema_fixture_handshake_accepts_shared_fixture_roots(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "dev/state/contract_registry.jsonl"
    registry_path.parent.mkdir(parents=True)
    root = "dev/test_data/schema_fixtures/DemoReceipt/1"
    rows = (
        {
            "contract_id": "DemoReceipt",
            "entry_kind": "artifact_schema",
            "python_owner_path": "dev/demo.py",
            "rust_owner_path": "",
            "fixture_path": root,
            "schema_version": 1,
            "ownership_mode": "python_only",
            "parity_command": "python3 dev/scripts/checks/check_schema_fixture_handshake.py --format json",
            "registry_path": "dev/state/contract_registry.jsonl",
            "registry_row_contract_id": "PlatformContractRegistryRow",
            "registry_row_schema_version": 1,
        },
        {
            "contract_id": "DemoReceipt",
            "entry_kind": "shared_contract",
            "python_owner_path": "dev/demo.py",
            "rust_owner_path": "",
            "fixture_path": root,
            "schema_version": 1,
            "ownership_mode": "python_only",
            "parity_command": "python3 dev/scripts/checks/check_schema_fixture_handshake.py --format json",
            "registry_path": "dev/state/contract_registry.jsonl",
            "registry_row_contract_id": "PlatformContractRegistryRow",
            "registry_row_schema_version": 1,
        },
    )
    registry_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    fixture_root = tmp_path / root
    (fixture_root / "valid").mkdir(parents=True)
    (fixture_root / "invalid").mkdir()
    for row in rows:
        valid = {
            "schema_fixture_contract_id": "PlatformSchemaFixture",
            "schema_fixture_version": 1,
            "fixture_role": "valid",
            "expected_result": "accept",
            "contract_id": row["contract_id"],
            "entry_kind": row["entry_kind"],
            "schema_version": 1,
        }
        schema_mismatch = {
            **valid,
            "fixture_role": "invalid",
            "expected_result": "reject",
            "invalid_reason": "schema_version_mismatch",
            "schema_version": 2,
        }
        missing_required = {
            **valid,
            "fixture_role": "invalid",
            "expected_result": "reject",
            "invalid_reason": "missing_required_field",
            "missing_field": "contract_id",
        }
        entry_kind = str(row["entry_kind"]).replace("_", "-")
        (fixture_root / f"valid/{entry_kind}-registry-row.json").write_text(
            json.dumps(valid, sort_keys=True),
            encoding="utf-8",
        )
        (
            fixture_root / f"invalid/{entry_kind}-schema-version-mismatch.json"
        ).write_text(
            json.dumps(schema_mismatch, sort_keys=True),
            encoding="utf-8",
        )
        (
            fixture_root / f"invalid/{entry_kind}-missing-required-field.json"
        ).write_text(
            json.dumps(missing_required, sort_keys=True),
            encoding="utf-8",
        )

    coverage, violations = evaluate_schema_fixture_handshake(repo_root=tmp_path)

    assert coverage["ok"] is True
    assert coverage["valid_fixtures_checked"] == 2
    assert coverage["invalid_fixtures_checked"] == 4
    assert violations == ()


def test_schema_fixture_handshake_flags_untracked_git_fixtures(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init")
    (tmp_path / ".gitignore").write_text("*.json\n", encoding="utf-8")
    registry_path = tmp_path / "dev/state/contract_registry.jsonl"
    registry_path.parent.mkdir(parents=True)
    row = {
        "contract_id": "IgnoredFixture",
        "entry_kind": "shared_contract",
        "python_owner_path": "dev/demo.py",
        "rust_owner_path": "",
        "fixture_path": "dev/test_data/schema_fixtures/IgnoredFixture/1",
        "schema_version": 1,
        "ownership_mode": "python_only",
        "parity_command": "python3 dev/scripts/checks/check_schema_fixture_handshake.py --format json",
        "registry_path": "dev/state/contract_registry.jsonl",
        "registry_row_contract_id": "PlatformContractRegistryRow",
        "registry_row_schema_version": 1,
    }
    registry_path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
    root = tmp_path / row["fixture_path"]
    (root / "valid").mkdir(parents=True)
    (root / "invalid").mkdir()
    valid = {
        "schema_fixture_contract_id": "PlatformSchemaFixture",
        "schema_fixture_version": 1,
        "fixture_role": "valid",
        "expected_result": "accept",
        "contract_id": "IgnoredFixture",
        "entry_kind": "shared_contract",
        "schema_version": 1,
    }
    missing_required = {
        **valid,
        "fixture_role": "invalid",
        "expected_result": "reject",
        "invalid_reason": "missing_required_field",
        "missing_field": "contract_id",
    }
    schema_mismatch = {
        **valid,
        "fixture_role": "invalid",
        "expected_result": "reject",
        "invalid_reason": "schema_version_mismatch",
        "schema_version": 2,
    }
    (root / "valid/registry-row.json").write_text(
        json.dumps(valid, sort_keys=True),
        encoding="utf-8",
    )
    (root / "invalid/missing-required-field.json").write_text(
        json.dumps(missing_required, sort_keys=True),
        encoding="utf-8",
    )
    (root / "invalid/schema-version-mismatch.json").write_text(
        json.dumps(schema_mismatch, sort_keys=True),
        encoding="utf-8",
    )

    coverage, violations = evaluate_schema_fixture_handshake(repo_root=tmp_path)

    assert coverage["ok"] is False
    assert coverage["git_tracking_enforced"] is True
    assert any(violation.rule == "untracked-fixture" for violation in violations)


def test_schema_version_monotonic_passes_current_repo() -> None:
    coverage, violations = evaluate_schema_version_monotonic()

    assert coverage["ok"] is True
    assert coverage["registry_row_count"] >= 1
    assert coverage["fixture_roots_checked"] == coverage["registry_row_count"]
    assert violations == ()


def test_schema_version_monotonic_flags_fixture_path_version_drift(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "dev/state/contract_registry.jsonl"
    registry_path.parent.mkdir(parents=True)
    row = {
        "contract_id": "DemoContract",
        "entry_kind": "shared_contract",
        "python_owner_path": "dev/demo.py",
        "rust_owner_path": "",
        "fixture_path": "dev/test_data/schema_fixtures/DemoContract/old",
        "schema_version": 2,
        "ownership_mode": "python_only",
        "parity_command": "python3 dev/scripts/checks/check_schema_version_monotonic.py --format json",
        "registry_path": "dev/state/contract_registry.jsonl",
        "registry_row_contract_id": "PlatformContractRegistryRow",
        "registry_row_schema_version": 1,
    }
    registry_path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    coverage, violations = evaluate_schema_version_monotonic(repo_root=tmp_path)

    assert coverage["ok"] is False
    assert any(
        violation.rule == "fixture-path-version-drift"
        and "DemoContract" == violation.contract_id
        for violation in violations
    )


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(
        ("git", "-C", str(repo_root), *args),
        check=True,
        capture_output=True,
        text=True,
    )
