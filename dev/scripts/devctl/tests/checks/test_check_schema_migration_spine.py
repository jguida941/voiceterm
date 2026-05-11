"""Tests for the schema migration spine guard."""

from __future__ import annotations

from dataclasses import replace

from dev.scripts.devctl.platform.schema_migration_spine import (
    durable_schema_policies,
    evaluate_schema_migration_spine,
)


def test_schema_migration_spine_passes_current_blueprint() -> None:
    coverage, violations = evaluate_schema_migration_spine()

    assert coverage["ok"] is True
    assert coverage["durable_contract_count"] >= 5
    assert coverage["policy_count"] >= coverage["durable_contract_count"]
    assert "RemoteControlCollaborationCampaign" in coverage[
        "planned_policy_contract_ids"
    ]
    assert violations == ()


def test_schema_migration_spine_flags_missing_durable_policy() -> None:
    policies = tuple(
        policy
        for policy in durable_schema_policies()
        if policy.contract_id != "PlanSourceSnapshot"
    )

    coverage, violations = evaluate_schema_migration_spine(policies=policies)

    assert coverage["ok"] is False
    assert any(
        violation.rule == "missing-durable-schema-policy"
        and violation.contract_id == "PlanSourceSnapshot"
        for violation in violations
    )


def test_schema_migration_spine_flags_registered_writer_without_authority() -> None:
    policies = list(durable_schema_policies())
    policies[0] = replace(
        policies[0],
        store_authority="",
        store_authority_status="registered_advisory",
    )

    coverage, violations = evaluate_schema_migration_spine(policies=tuple(policies))

    assert coverage["ok"] is False
    assert any(
        violation.rule == "registered-store-authority-missing"
        and violation.contract_id == policies[0].contract_id
        for violation in violations
    )
