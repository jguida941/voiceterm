"""Tests for the platform-contract sync guard."""

from __future__ import annotations

from dataclasses import replace

from dev.scripts.checks.platform_contract_sync.report import build_report, render_md
from dev.scripts.checks.platform_contract_sync.support import evaluate_platform_contract_sync
from dev.scripts.devctl.platform.blueprint import build_platform_blueprint


def _drop_contract_field(contract_id: str, field_name: str):
    blueprint = build_platform_blueprint()
    shared_contracts = []
    for contract in blueprint.shared_contracts:
        if contract.contract_id != contract_id:
            shared_contracts.append(contract)
            continue
        shared_contracts.append(
            replace(
                contract,
                required_fields=tuple(
                    field for field in contract.required_fields if field.name != field_name
                ),
            )
        )
    return replace(blueprint, shared_contracts=tuple(shared_contracts))


def test_platform_contract_sync_passes_on_current_blueprint() -> None:
    report = build_report()
    assert report["ok"] is True
    assert report["violations"] == []


def test_platform_contract_sync_flags_missing_service_lifecycle_field() -> None:
    blueprint = _drop_contract_field("LocalServiceEndpoint", "shutdown_entrypoints")
    _coverage, violations = evaluate_platform_contract_sync(blueprint)
    assert len(violations) == 1
    assert violations[0]["contract_id"] == "LocalServiceEndpoint"
    assert violations[0]["missing_fields"] == ("shutdown_entrypoints",)


def test_platform_contract_sync_flags_missing_caller_authority_field() -> None:
    blueprint = _drop_contract_field("CallerAuthorityPolicy", "forbidden_actions")
    _coverage, violations = evaluate_platform_contract_sync(blueprint)
    assert len(violations) == 1
    assert violations[0]["contract_id"] == "CallerAuthorityPolicy"
    assert violations[0]["missing_fields"] == ("forbidden_actions",)


def test_platform_contract_sync_markdown_lists_violations() -> None:
    blueprint = _drop_contract_field("CallerAuthorityPolicy", "forbidden_actions")
    coverage, violations = evaluate_platform_contract_sync(blueprint)
    report = {
        "command": "check_platform_contract_sync",
        "ok": False,
        "checked_contracts": len(coverage),
        "violations": list(violations),
        "coverage": list(coverage),
    }
    output = render_md(report)
    assert "# check_platform_contract_sync" in output
    assert "forbidden_actions" in output
