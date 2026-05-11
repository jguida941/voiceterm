"""Tests for the check CLI/focused-test parity guard."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.check_check_cli_test_parity import (
    CheckCliTestParityTarget,
    evaluate_check_cli_test_parity,
)


def test_check_cli_test_parity_passes_current_managed_targets() -> None:
    coverage, violations = evaluate_check_cli_test_parity()

    assert coverage["ok"] is True
    assert coverage["managed_target_count"] >= 6
    assert "schema_migration_spine" in {
        str(target["check_id"]) for target in coverage["targets"]
    }
    assert violations == ()


def test_check_cli_test_parity_flags_cli_missing_shared_contract(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "dev/scripts/checks/check_demo.py", "def main(): pass\n")
    _write(
        tmp_path,
        "dev/scripts/devctl/tests/checks/test_check_demo.py",
        "from dev.scripts.checks.check_demo import build_report\n",
    )
    target = CheckCliTestParityTarget(
        check_id="demo",
        check_script_path="dev/scripts/checks/check_demo.py",
        cli_contract_paths=("dev/scripts/checks/check_demo.py",),
        test_contract_paths=("dev/scripts/devctl/tests/checks/test_check_demo.py",),
        shared_tokens=("build_report",),
    )

    coverage, violations = evaluate_check_cli_test_parity(
        repo_root=tmp_path,
        targets=(target,),
        catalog_paths={"demo": "dev/scripts/checks/check_demo.py"},
    )

    assert coverage["ok"] is False
    assert any(
        violation.rule == "cli-shared-token-missing"
        and violation.check_id == "demo"
        for violation in violations
    )


def test_check_cli_test_parity_flags_test_missing_shared_contract(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "dev/scripts/checks/check_demo.py",
        "def build_report(): return {'ok': True}\n",
    )
    _write(
        tmp_path,
        "dev/scripts/devctl/tests/checks/test_check_demo.py",
        "def test_demo(): assert True\n",
    )
    target = CheckCliTestParityTarget(
        check_id="demo",
        check_script_path="dev/scripts/checks/check_demo.py",
        cli_contract_paths=("dev/scripts/checks/check_demo.py",),
        test_contract_paths=("dev/scripts/devctl/tests/checks/test_check_demo.py",),
        shared_tokens=("build_report",),
    )

    coverage, violations = evaluate_check_cli_test_parity(
        repo_root=tmp_path,
        targets=(target,),
        catalog_paths={"demo": "dev/scripts/checks/check_demo.py"},
    )

    assert coverage["ok"] is False
    assert any(
        violation.rule == "test-shared-token-missing"
        and violation.check_id == "demo"
        for violation in violations
    )


def test_check_cli_test_parity_flags_script_catalog_drift(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "dev/scripts/checks/check_demo.py",
        "def build_report(): return {'ok': True}\n",
    )
    _write(
        tmp_path,
        "dev/scripts/devctl/tests/checks/test_check_demo.py",
        "from dev.scripts.checks.check_demo import build_report\n",
    )
    target = CheckCliTestParityTarget(
        check_id="demo",
        check_script_path="dev/scripts/checks/check_demo.py",
        cli_contract_paths=("dev/scripts/checks/check_demo.py",),
        test_contract_paths=("dev/scripts/devctl/tests/checks/test_check_demo.py",),
        shared_tokens=("build_report",),
    )

    coverage, violations = evaluate_check_cli_test_parity(
        repo_root=tmp_path,
        targets=(target,),
        catalog_paths={"demo": "dev/scripts/checks/check_other.py"},
    )

    assert coverage["ok"] is False
    assert any(
        violation.rule == "registered-check-path-drift"
        and violation.check_id == "demo"
        for violation in violations
    )


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
